import threading
import paramiko
import os
from .display import display_stories, display_about_page, display_faq_page, display_story_details
from .api import fetch_top_stories, fetch_story_details
from .utils import clear_screen


def load_or_generate_ssh_key(key_path):
    """
    Load an RSA key from a given path, or generate and save a new key if it does not exist.
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(key_path), exist_ok=True)

    if os.path.exists(key_path):
        try:
            return paramiko.RSAKey(filename=key_path)
        except IOError as e:
            print(f"Failed to load existing SSH key due to: {str(e)}. Generating a new key.")

    # Generate a new key and save it if not found or loading failed
    host_key = paramiko.RSAKey.generate(2048)
    try:
        host_key.write_private_key_file(key_path)
        os.chmod(key_path, 0o600)  # Set file permission to read/write for the owner only
        print(f"Generated new SSH host key and saved to {key_path}.")
    except IOError as e:
        print(f"Failed to save the SSH key to {key_path} due to: {str(e)}")
    return host_key

# Set up host key using a user-specific directory
user_home_dir = os.path.expanduser('~')
key_file_path = os.path.join(user_home_dir, '.ssh', 'ssh_host_rsa_key')
host_key = load_or_generate_ssh_key(key_file_path)


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
        self.terminal_width = width
        self.terminal_height = height
        return True

    def check_channel_window_change_request(self, channel, width, height, pixelwidth, pixelheight):
        # Update terminal size when the client resizes their terminal
        self.terminal_width = width
        self.terminal_height = height
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
                display_stories(channel, top_story_ids, cursor_index, server.terminal_width, server.terminal_height)
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

