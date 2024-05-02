import paramiko
import socket
import threading
import requests
import humanize
import datetime
import os

# Set up host key
host_key = paramiko.RSAKey.generate(2048)


# Fetch top stories once to minimize API calls and load details on demand
def fetch_top_stories():
    response = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json')
    return response.json()[:200]  # Fetching top 200 story IDs

def fetch_story_details(story_id):
    response = requests.get(f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json')
    if response.status_code == 200:
        return response.json()
    return None

def display_stories(channel, top_story_ids, story_cache, cursor_index):
    try:
        rows, columns = os.popen('stty size', 'r').read().split()
        rows = int(rows)
        page_size = (rows - 5) // 2  # Adjusting page size for multi-line entries
    except ValueError:
        page_size = 20  # Default page size if terminal size fetch fails

    clear_screen(channel)

    # Calculate visible slice of the list based on the cursor position
    start_index = max(0, cursor_index - (page_size // 2))
    end_index = min(len(top_story_ids), start_index + page_size)

    message = "\rTop Hacker News Stories:\n"
    for i in range(start_index, end_index):
        story_id = top_story_ids[i]
        story = story_cache.get(story_id, None)

        if story is None:
            story_cache[story_id] = fetch_story_details(story_id)  # Fetch details if not in cache
            story = story_cache[story_id]

        if story == "Loading..." or story is None:
            title = "Loading story details..."
            url = points = author = time_ago = comments = "Loading..."
        else:
            title = story.get('title', 'No title available')
            url = story.get('url', 'No URL')
            points = story.get('score', 0)
            author = story.get('by', 'Unknown')
            comments = story.get('descendants', 0)
            time_posted = datetime.datetime.fromtimestamp(story['time'])
            time_ago = humanize.naturaltime(datetime.datetime.now() - time_posted)

        selected = '*' if i == cursor_index else ' '
        message += f"\n\r{selected}{i + 1}. {title} ({url})\n\r   {points} points by {author} {time_ago} | {comments} comments"

    message += "\n\rUse [Up Arrow] and [Down Arrow] to navigate, 'C' to convert, 'Q' to quit."
    channel.send(message.encode('utf-8'))


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
    story_cache = {}  # Dictionary to cache story details
    cursor_index = 0

    try:
        while True:
            display_stories(channel, top_story_ids, story_cache, cursor_index)
            inputs = channel.recv(1024).decode('utf-8').strip()

            if 'Q' in inputs.upper():
                break
            elif '\x1b[B' in inputs and cursor_index < len(top_story_ids) - 1:  # Down Arrow
                cursor_index += 1
            elif '\x1b[A' in inputs and cursor_index > 0:  # Up Arrow
                cursor_index -= 1

    finally:
        clear_screen(channel)
        channel.close()
        transport.close()


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

