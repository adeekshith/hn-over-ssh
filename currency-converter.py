import paramiko
import socket
import threading
import requests
import os

# Set up host key
host_key = paramiko.RSAKey.generate(2048)

popular_currencies = ['EUR', 'GBP', 'CAD', 'AUD', 'JPY', 'CHF', 'CNY', 'SEK', 'NZD', 'MXN']

def clear_screen(channel):
    # Clear the screen and scrollback buffer, then reset cursor position
    clear_command = "\x1b[3J\x1b[2J\x1b[H".encode('utf-8')
    channel.send(clear_command)
    channel.send("".encode('utf-8'))  # Send an empty message to ensure flush
    channel.send(clear_command)


def fetch_conversion_rates():
    url = "https://open.er-api.com/v6/latest/USD"
    response = requests.get(url)
    data = response.json()
    if data['result'] == 'success':
        return data['rates']
    else:
        raise Exception("Failed to fetch currency rates")

# Fetch rates when the server starts
conversion_rates = fetch_conversion_rates()


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


def display_currency_menu(channel, conversion_rates, selected_currencies, page=0):
    # Determine terminal size and page size
    try:
        rows, columns = os.popen('stty size', 'r').read().split()
        page_size = int(rows) - 5  # Less space for prompts and commands
    except ValueError:
        page_size = 20  # Fallback if terminal size can't be determined

    # Clear the screen and reset cursor
    clear_screen(channel)

    # Generate the list of currencies for current page
    message = f"Available Currencies (Page {page + 1}):\n"
    currency_items = list(conversion_rates.items())
    start_index = page * page_size
    end_index = min(start_index + page_size, len(currency_items))

    for index, (currency, rate) in enumerate(currency_items[start_index:end_index], start=start_index):
        selected = '*' if currency in selected_currencies else ' '
        message += f"\r{index + 1}. {currency} ({rate:.4f}) {selected}\n"

    # Navigation controls
    if page > 0:
        message += "\n\r[Up Arrow] Previous Page"
    if end_index < len(currency_items):
        message += "\n\r[Down Arrow] Next Page"

    message += "\n\r'C' to convert, 'Q' to quit."
    channel.send(message.encode('utf-8'))

    return start_index, end_index, len(currency_items) > end_index



def handle_client(client_socket, conversion_rates, popular_currencies):
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

    server.event.wait()

    selected_currencies = popular_currencies[:]
    current_page = 0

    try:
        while True:
            start_index, end_index, more_pages = display_currency_menu(channel, conversion_rates, selected_currencies, current_page)
            inputs = channel.recv(1024).decode('utf-8').strip()

            if 'Q' in inputs.upper():
                break
            elif 'C' in inputs.upper():
                channel.send("\rEnter amount in USD to convert: ".encode('utf-8'))
                amount_str = channel.recv(1024).decode('utf-8').strip()
                try:
                    amount = float(amount_str)
                    result = '\n\rConversions:\n'
                    for currency in selected_currencies:
                        rate = conversion_rates[currency]
                        converted_amount = amount * rate
                        result += f"\r{amount} USD is {converted_amount:.2f} {currency}\n"
                    channel.send(result.encode('utf-8'))
                except ValueError:
                    channel.send("\rInvalid amount. Please enter a valid number.\n".encode('utf-8'))
            elif '\x1b[B' in inputs and more_pages:
                current_page += 1
            elif '\x1b[A' in inputs and current_page > 0:
                current_page -= 1

    finally:
        clear_screen(channel)
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
        client_thread = threading.Thread(target=handle_client, args=(client, conversion_rates, popular_currencies))
        client_thread.start()

if __name__ == '__main__':
    start_server()

