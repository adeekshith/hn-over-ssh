import paramiko
import socket
import threading
import requests
import humanize
import datetime
import os
import time
from threading import Lock

# Set up host key
host_key = paramiko.RSAKey.generate(2048)

# Global cache to store both story details and top story IDs
cache = {
    'top_stories': {
        'data': None,
        'timestamp': None
    },
    'stories': {}
}

cache_lock = Lock()

# Fetch top stories once to minimize API calls and load details on demand
def fetch_top_stories():
    current_time = time.time()
    
    with cache_lock:  # Acquire lock to ensure thread-safe access to the cache
        # Check if cached data is still valid (e.g., cache for 10 minutes)
        if (cache['top_stories']['data'] is not None and 
            (current_time - cache['top_stories']['timestamp']) < 600):
            return cache['top_stories']['data']

    # If the cache is empty or stale, fetch new data
    response = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json')
    if response.status_code == 200:
        with cache_lock:  # Again, ensure thread safety when updating the cache
            # Update cache with new data and current timestamp
            cache['top_stories']['data'] = response.json()[:200]  # Top 200 stories
            cache['top_stories']['timestamp'] = current_time
        return cache['top_stories']['data']
    else:
        # Use old data if it exists when the API call fails, ensuring some data is always available
        with cache_lock:
            return cache['top_stories']['data'] if cache['top_stories']['data'] is not None else []


def fetch_story_details(story_id):
    current_time = time.time()
    
    with cache_lock:
        story_cache = cache['stories'].get(story_id, {})

    if story_cache and (current_time - story_cache.get('timestamp', 0) < 900):
        return story_cache['data']
    
    response = requests.get(f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json')
    if response.status_code == 200:
        with cache_lock:
            cache['stories'][story_id] = {
                'data': response.json(),
                'timestamp': current_time
            }
        return cache['stories'][story_id]['data']
    else:
        return story_cache['data'] if story_cache else None



def display_about_page(channel):
    clear_screen(channel)
    about_message = (
        "\r┌────┬───────┬─────────┬───────┐\n"
        "\r│ HN │ t top │ a about │ f faq │\n"
        "\r└────┴───────┴─────────┴───────┘\n"
        "\r\n"
        "\rAbout Hacker News Client\n"
        "\r------------------------\n"
        "\rDeveloped by: [Your Name]\n"
        "\rContact: [Your Email]\n"
        "\rVersion: 1.0.0\n"
        "\rDescription: This is a custom SSH client for browsing Hacker News interactively.\n"
        "\r────────────────────────────────\n\r     ↑ Up   ↓ Down   q quit\n"
    )
    channel.send(about_message.encode('utf-8'))

def display_faq_page(channel):
    clear_screen(channel)
    faq_message = (
        "\r┌────┬───────┬─────────┬───────┐\n"
        "\r│ HN │ t top │ a about │ f faq │\n"
        "\r└────┴───────┴─────────┴───────┘\n"
        "\r\n"
        "\rFAQ - Frequently Asked Questions\n"
        "\r--------------------------------\n"
        "\rQ1: How do I navigate the stories?\n"
        "\rA1: Use the arrow keys to move up and down through the list of stories.\n"
        "\r\n"
        "\rQ2: How can I quit the application?\n"
        "\rA2: Press 'q' to quit the application at any time.\n"
        "\r────────────────────────────────\n\r     ↑ Up   ↓ Down   q quit\n"
    )
    channel.send(faq_message.encode('utf-8'))



def display_stories(channel, top_story_ids, cursor_index):
    rows, columns = os.popen('stty size', 'r').read().split()
    page_size = ((int(rows) // 2) - 9)  # Adjust for top menu and footer and multi line rows

    clear_screen(channel)

    # Top Menu
    message = (
        "\r┌────┬───────┬─────────┬───────┐\n"
        "\r│ HN │ t top │ a about │ f faq │\n"
        "\r└────┴───────┴─────────┴───────┘\n"
    )

    start_index = max(0, cursor_index - (page_size // 2))
    end_index = min(len(top_story_ids), start_index + page_size)

    # Stories List
    for i in range(start_index, end_index):
        story_id = top_story_ids[i]
        story = fetch_story_details(story_id)
        if not story:  # If still loading or failed to load
            story = {"title": "Loading...", "url": "#", "score": "Loading...", "by": "Loading...", "descendants": "Loading...", "time": datetime.datetime.now().timestamp()}
        
        title = story.get('title', 'No title available')
        url = story.get('url', '#')
        points = story.get('score', '0')
        author = story.get('by', 'Unknown')
        comments = story.get('descendants', '0')
        time_posted = datetime.datetime.fromtimestamp(story['time'])
        time_ago = humanize.naturaltime(datetime.datetime.now() - time_posted)
        
        selected = '*' if i == cursor_index else ' '
        message += f"\r{selected}{i + 1}. {title} ({url})\n\r    {points} points by {author} {time_ago} | {comments} comments\n"

    # Footer
    message += "\r────────────────────────────────\n\r     ↑ Up   ↓ Down   q quit\n"
    channel.send(message.encode('utf-8'))


def display_story_details(channel, story_id):
    story = fetch_story_details(story_id)
    if not story:
        story = {"title": "Story details loading failed", "by": "Unknown", "time": time.time(), "score": 0, "url": "#", "text": "No additional information.", "kids": []}

    clear_screen(channel)
    time_posted = datetime.datetime.fromtimestamp(story['time'])
    time_ago = humanize.naturaltime(datetime.datetime.now() - time_posted)
    message = (
        "\r┌────┬───────┬─────────┬───────┐\n"
        "\r│ HN │ t top │ a about │ f faq │\n"
        "\r└────┴───────┴─────────┴───────┘\n"
        f"\r{story['title']}\n"
        f"\r{story.get('url', '')}\n"
        f"\r{story['score']} points by {story['by']} {time_ago} | {story.get('descendants', 0)} comments\n"
        f"\r{story.get('text', '')}\n"
        "\r────────────────────────────────\n"
    )
    channel.send(message.encode('utf-8'))

    # Display comments if they exist
    if 'kids' in story and story['kids']:
        for kid_id in story['kids']:
            kid_story = fetch_story_details(kid_id)
            kid_message = (
                f"\n\r• {kid_story.get('by', 'Unknown')}: {kid_story.get('text', 'No text available.')}\n"
            )
            channel.send(kid_message.encode('utf-8'))
    channel.send("\r────────────────────────────────\n\r     ↑ Up   ↓ Down   q quit\n".encode('utf-8'))



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

            inputs = channel.recv(1024).decode('utf-8')
            # print(repr(inputs)) # debug
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
                display_story_details(channel, top_story_ids[cursor_index])

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

