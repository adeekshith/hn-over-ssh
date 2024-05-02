import paramiko
import socket

# Set up host key
host_key = paramiko.RSAKey.generate(2048)

conversion_rates = {
    'INR': 82.97,
    'EUR': 0.93,
    'GBP': 0.81
}

class Server(paramiko.ServerInterface):
    def __init__(self):
        pass

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        if username == 'user' and password == 'pass':
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_channel_shell_request(self, channel):
        return True

def handle_client(client_socket):
    transport = paramiko.Transport(client_socket)
    transport.add_server_key(host_key)

    server = Server()
    transport.start_server(server=server)

    channel = transport.accept(20)
    if channel is None:
        print("No channel.")
        transport.close()
        return

    try:
        channel.send("Enter amount in USD to convert: ".encode('utf-8'))
        while True:
            f = channel.makefile('rU')
            amount_str = f.readline().strip()
            if amount_str:
                try:
                    amount = float(amount_str)
                    result = 'Conversions:\n'
                    for currency, rate in conversion_rates.items():
                        converted_amount = amount * rate
                        result += f'{amount} USD is {converted_amount:.2f} {currency}\n'
                    channel.send(result.encode('utf-8'))
                    channel.send("Enter amount in USD to convert: ".encode('utf-8'))
                except ValueError:
                    channel.send('Please enter a valid number.\n'.encode('utf-8'))
    except Exception as e:
        print(f"Caught exception: {str(e)}")
    finally:
        channel.close()
        transport.close()

if __name__ == '__main__':
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('localhost', 2200))
    server_socket.listen(100)
    print('Listening for connection ...')

    while True:
        client, addr = server_socket.accept()
        print(f'Got a connection from {addr[0]}:{addr[1]}')
        handle_client(client)

