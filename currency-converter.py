import paramiko
import socket
import threading

# Set up host key
host_key = paramiko.RSAKey.generate(2048)

conversion_rates = {
    'INR': 82.97,  # Example rate: 1 USD = 82.97 INR
    'EUR': 0.93,   # Example rate: 1 USD = 0.93 EUR
    'GBP': 0.81    # Example rate: 1 USD = 0.81 GBP
}

def clear_screen(channel):
    # Clear the screen and scrollback buffer, then reset cursor position
    clear_command = "\x1b[3J\x1b[2J\x1b[H".encode('utf-8')
    channel.send(clear_command)
    channel.send("".encode('utf-8'))  # Send an empty message to ensure flush
    channel.send(clear_command)


class Server(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        return paramiko.AUTH_SUCCESSFUL

    def check_auth_none(self, username):
        return paramiko.AUTH_SUCCESSFUL

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

def handle_client(client_socket):
    transport = paramiko.Transport(client_socket)
    transport.add_server_key(host_key)

    server = Server()
    try:
        transport.start_server(server=server)
    except paramiko.SSHException:
        print("SSH negotiation failed.")
        transport.close()
        return

    channel = transport.accept(timeout=20)
    if channel is None:
        print("No channel.")
        transport.close()
        return

    server.event.wait()  # Wait for the shell request

    try:
        clear_screen(channel)  # Clear the screen at the start
        channel.send("Enter amount in USD to convert: ".encode('utf-8'))

        while True:
            command = channel.recv(1024).decode('utf-8').strip()
            if not command:
                print("Connection closed by client.")
                break

            try:
                amount = float(command)
                result = '\r\nConversions:\n'  # Ensure new lines start correctly
                for currency, rate in conversion_rates.items():
                    converted_amount = amount * rate
                    result += f'\r{amount} USD is {converted_amount:.2f} {currency}\n'
                clear_screen(channel)  # Clear before displaying new results
                channel.send(result.encode('utf-8'))
            except ValueError:
                clear_screen(channel)  # Clear before displaying the error message
                channel.send('\r\nPlease enter a valid number.\r\n'.encode('utf-8'))

            channel.send("\rEnter amount in USD to convert: ".encode('utf-8'))
    except Exception as e:
        print(f"Caught exception: {str(e)}")
    finally:
        channel.close()
        transport.close()


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('localhost', 2200))
    server_socket.listen(100)
    print('Listening for connection ...')

    while True:
        client, addr = server_socket.accept()
        print(f'Got a connection from {addr[0]}:{addr[1]}')
        client_thread = threading.Thread(target=handle_client, args=(client,))
        client_thread.start()

if __name__ == '__main__':
    start_server()

