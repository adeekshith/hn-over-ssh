import datetime
import humanize
import os
from hacker_news_ssh.api import fetch_top_stories, fetch_story_details
from hacker_news_ssh.utils import clear_screen


def display_about_page(channel):
    clear_screen(channel)
    about_message = (
        "\r     ┌────┬───────┬─────────┬───────┐\n"
        "\r     │ HN │ t top │ a about │ f faq │\n"
        "\r     └────┴───────┴─────────┴───────┘\n"
        "\r\n"
        "\rWelcome to Hacker News Over SSH\n"
        "\r--------------------------------\n"
        "\rRead Hacker News at the comfort of your terminal. This project provides\n"
        "\ra simple, terminal-based interface to browse Hacker News articles and comments.\n"
        "\rSource code is available at: https://github.com/adeekshith/hn-over-ssh\n"
        "\r\n"
        "\rAbout the Developer\n"
        "\r-------------------\n"
        "\rDeveloped by: Deekshith Allamaneni\n"
        "\rContact:\n"
        "\r- Website: https://meet.deekshith.in\n"
        "\r- GitHub: https://github.com/adeekshith\n"
        "\r- Mastodon: https://techhub.social/@dsoft (@dsoft@techhub.social)\n"
        "\r- LinkedIn: https://www.linkedin.com/in/adeekshith\n"
        "\r\n"
        "\rLooking for Opportunities\n"
        "\r-------------------------\n"
        "\rI was impacted by recent layoffs and am actively seeking new opportunities.\n"
        "\rWith over 10 years of experience building large scale distributed systems and\n"
        "\rproficiency in Java, Python, GoLang, JavaScript, Kotlin, among others,\n"
        "\rI have also developed projects on the side that have accumulated millions of downloads.\n"
        "\rIf you have or know of relevant opportunities, please let me know!\n"
        "\r\n"
        "\r───────────┬──────────┬────────────┬─────────────\n\r     ↑ Up  │  ↓ Down  │  Esc Back  │  q Quit\n"
    )
    channel.send(about_message.encode('utf-8'))


def display_faq_page(channel):
    clear_screen(channel)
    faq_message = (
        "\r     ┌────┬───────┬─────────┬───────┐\n"
        "\r     │ HN │ t top │ a about │ f faq │\n"
        "\r     └────┴───────┴─────────┴───────┘\n"
        "\r\n"
        "\rFAQ - Frequently Asked Questions\n"
        "\r--------------------------------\n"
        "\rQ1: How do I navigate the stories?\n"
        "\rA1: Use the arrow keys to move up and down through the list of stories and Esc to go back\n"
        "\r\n"
        "\rQ2: How can I quit the application?\n"
        "\rA2: Press 'q' to quit the application at any time.\n"
        "\r───────────┬──────────┬────────────┬─────────────\n\r     ↑ Up  │  ↓ Down  │  Esc Back  │  q Quit\n"
    )
    channel.send(faq_message.encode('utf-8'))


def display_stories(channel, top_story_ids, cursor_index, terminal_width, terminal_height):
    # Convert string to integers
    rows, columns = max(terminal_height, 24), max(terminal_width, 80)
    page_size = ((int(rows) // 2) - 5)  # Adjust for top menu and footer and multi line rows

    clear_screen(channel)

    # Top Menu
    message = (
        "\r     ┌────┬───────┬─────────┬───────┐\n"
        "\r     │ HN │ t top │ a about │ f faq │\n"
        "\r     └────┴───────┴─────────┴───────┘\n"
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
    message += "\r───────────┬──────────┬────────────┬─────────────\n\r     ↑ Up  │  ↓ Down  │  Esc Back  │  q Quit\n"
    channel.send(message.encode('utf-8'))


def display_story_details(channel, story_id):
    story = fetch_story_details(story_id)
    if not story:
        story = {"title": "Story details loading failed", "by": "Unknown", "time": time.time(), "score": 0, "url": "#", "text": "No additional information.", "kids": []}

    clear_screen(channel)
    time_posted = datetime.datetime.fromtimestamp(story['time'])
    time_ago = humanize.naturaltime(datetime.datetime.now() - time_posted)
    message = (
        "\r     ┌────┬───────┬─────────┬───────┐\n"
        "\r     │ HN │ t top │ a about │ f faq │\n"
        "\r     └────┴───────┴─────────┴───────┘\n"
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
    channel.send("\r───────────┬──────────┬────────────┬─────────────\n\r     ↑ Up  │  ↓ Down  │  Esc Back  │  q Quit\n".encode('utf-8'))


