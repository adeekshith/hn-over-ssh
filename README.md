# Hacker News Over SSH

Hacker News Over SSH allows users to interact with Hacker News through a terminal over SSH. This SSH-based client enables browsing Hacker News stories, viewing detailed descriptions, and reading comments in a terminal interface.

## Demo

Open your terminal and type the following command:


```
$ ssh hn.parishod.com
```

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

It is currently working but not feature complete. Only top level comments are being shown and pagination for comments are not implemented yet. UI layout can be improved as well. Feel free to raise PRs to fix any minor issues but please raise an issue and discuss first if you are planning to implement any major features. Thank you!

## Hire me

I was impacted by recent laid offs and looking for new opportunities. I am open to roles and consulting opportunities. Connect with me on [LinkedIn](https://www.linkedin.com/in/adeekshith) and [Mastodon](https://techhub.social/@dsoft) (`@dsoft@techhub.social`).

