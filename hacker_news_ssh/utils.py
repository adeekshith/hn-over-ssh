"""
This module provides utility functions to support the Hacker News SSH client functionalities.
It includes a function to clear the display screen on the client terminal.
"""

def clear_screen(channel):
    """
    Clears the display screen of the SSH client's terminal. 
    Sends escape sequences to reset the terminal display and cursor position.
    """
    # Clear the screen and scrollback buffer, then reset cursor position
    clear_command = "\x1b[3J\x1b[2J\x1b[H".encode('utf-8')
    channel.send(clear_command)
    channel.send("".encode('utf-8'))  # Send an empty message to ensure flush
    channel.send(clear_command)
