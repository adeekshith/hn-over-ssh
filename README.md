# Hacker News Over SSH

Hacker News Over SSH allows users to interact with Hacker News through a terminal over SSH. This SSH-based client enables browsing Hacker News stories, viewing detailed descriptions, and reading comments in a terminal interface.

## Features

- Browse top stories from Hacker News.
- View detailed story information including title, author, score, and URL.
- Read comments and discussions related to stories.

## Installation

Clone this repository:

```bash
git clone https://github.com/yourusername/hacker-news-over-ssh.git
cd hacker-news-over-ssh
```

Install required dependencies:

```
pip install -r requirements.txt
```

## Usage:

Run the server:

```
python server.py
```

Connect to the server using an SSH client:

```
ssh -p 2200 user@host
```

## Development

To set up a development environment, install the development dependencies:

```bash
pip install -r requirements-dev.txt
```

