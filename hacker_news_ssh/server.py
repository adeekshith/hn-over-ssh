"""
This module creates and manages a server for the Hacker News SSH service.
It listens for incoming connections and handles them using a dedicated client handler.
"""

import socket
import threading
from hacker_news_ssh.client_handler import handle_client

def start_server():
    """
    Starts the server, listens for incoming connections, and spawns a new thread
    for each connection to handle client requests.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 2200))
    server_socket.listen(100)
    print('Listening for connection ...')

    while True:
        client, addr = server_socket.accept()
        print(f'Got a connection from {addr[0]}:{addr[1]}')
        client_thread = threading.Thread(target=handle_client, args=(client,))
        client_thread.start()

if __name__ == '__main__':
    start_server()
