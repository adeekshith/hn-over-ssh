"""
This module interacts with the Hacker News API to fetch and cache top stories and story details.
"""

import time
from threading import Lock
import requests

cache = {
    'top_stories': {
        'data': None,
        'timestamp': None
    },
    'stories': {}
}

cache_lock = Lock()

def fetch_top_stories():
    """Fetch top stories from Hacker News, using cache if available and recent."""
    current_time = time.time()
    with cache_lock:
        if cache['top_stories']['data'] is not None and (current_time - cache['top_stories']['timestamp']) < 600:
            return cache['top_stories']['data']

    response = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json')
    if response.status_code == 200:
        with cache_lock:
            cache['top_stories']['data'] = response.json()[:200]
            cache['top_stories']['timestamp'] = current_time
        return cache['top_stories']['data']
    return []

def fetch_story_details(story_id):
    """Fetch details for a specific story by ID, using cache if available and recent."""
    current_time = time.time()
    with cache_lock:
        story_cache = cache['stories'].get(story_id, {})
    if story_cache and (current_time - story_cache.get('timestamp', 0) < 900):
        return story_cache['data']

    response = requests.get(f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json')
    if response.status_code == 200:
        with cache_lock:
            cache['stories'][story_id] = {'data': response.json(), 'timestamp': current_time}
        return cache['stories'][story_id]['data']
    return story_cache['data'] if story_cache else None
