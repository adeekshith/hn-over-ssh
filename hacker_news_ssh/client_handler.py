import threading
import paramiko
from .display import display_stories, display_about_page, display_faq_page, display_story_details
from .api import fetch_top_stories, fetch_story_details
from .utils import clear_screen

# Set up host key
host_key = paramiko.RSAKey.generate(2048)

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

    server.event.wait()

    top_story_ids = fetch_top_stories()
    cursor_index = 0
    current_view = 'top'  # Manage different views: 'top', 'about', 'faq', 'story'

    try:
        while True:
            if current_view == 'top':
                display_stories(channel, top_story_ids, cursor_index)
            elif current_view == 'about':
                display_about_page(channel)
            elif current_view == 'faq':
                display_faq_page(channel)
            elif current_view == 'story':
                display_story_details(channel, top_story_ids[cursor_index])

            inputs = channel.recv(1024).decode('utf-8')
            if inputs.lower() == 'q':
                break
            elif inputs.lower() == 't' or inputs == '\x1b':
                current_view = 'top'
            elif inputs.lower() == 'a':
                current_view = 'about'
            elif inputs.lower() == 'f':
                current_view = 'faq'
            elif inputs == '\x1b[A' and current_view == 'top' and cursor_index > 0:  # Up Arrow
                cursor_index -= 1
            elif inputs == '\x1b[B' and current_view == 'top' and cursor_index < len(top_story_ids) - 1:  # Down Arrow
                cursor_index += 1
            elif inputs in ('\r', '\n', '\r\n') and current_view == 'top':  # Handle Enter key for different systems
                current_view = 'story'

    finally:
        clear_screen(channel)
        channel.close()
        transport.close()

