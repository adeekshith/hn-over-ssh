# Hacker News Over SSH

Hacker News Over SSH allows users to interact with Hacker News through a terminal over SSH. This SSH-based client enables browsing Hacker News stories, viewing detailed descriptions, and reading comments in a terminal interface.

Screencast: https://youtu.be/Qjfih0GYTJk


<a href="https://asciinema.org/a/657871" target="_blank"><img src="https://asciinema.org/a/657871.svg" alt="image" width="90%" height="auto" /></a>


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
# (Optional) Create virtual env
python -m venv venv
source venv/bin/activate
```

```
pip3 install -r requirements.txt
```

## Usage:

Run the server:

```
python3 -m hacker_news_ssh.server
```

Connect to the server using an SSH client:

```
ssh -p 2200 localhost
```

## Development

To set up a development environment, install the development dependencies:

```bash
pip install -r requirements-dev.txt
```

