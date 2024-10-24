import requests
import random
import os
import json
from datetime import datetime, timedelta
from requests_oauthlib import OAuth1Session
import time

# Twitter API configurations for both accounts
TWITTER_ACCOUNTS = {
    'account1': {
        'consumer_key': os.environ.get('CONSUMER_KEY'),
        'consumer_secret': os.environ.get('CONSUMER_SECRET'),
        'access_token': os.environ.get('ACCESS_TOKEN'),
        'access_token_secret': os.environ.get('ACCESS_SECRET')
    },
    'account2': {
        'consumer_key': os.environ.get('CONSUMER_KEY'),
        'consumer_secret': os.environ.get('CONSUMER_SECRET'),
        'access_token': os.environ.get('ACCESS_TOKEN2'),
        'access_token_secret': os.environ.get('ACCESS_SECRET2')
    }
}

API_URL_POST = 'https://api.twitter.com/2/tweets'
REPO_OWNER = 'likhonisaac'
REPO_NAME = 'Terminals-Pumps'
HISTORY_FILE = 'post_history.json'

class TwitterBot:
    def __init__(self):
        self.posts_history = self.load_posts_history()
        
    def load_posts_history(self):
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r') as file:
                    return json.load(file)
        except Exception as e:
            print(f"Error loading history: {e}")
        return {'account1': {}, 'account2': {}}

    def save_posts_history(self):
        try:
            with open(HISTORY_FILE, 'w') as file:
                json.dump(self.posts_history, file, indent=2)
            print(f"Successfully saved history to {HISTORY_FILE}")
        except Exception as e:
            print(f"Error saving history: {e}")

    def load_posts(self):
        try:
            url = f'https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/post/post.json'
            response = requests.get(url)
            response.raise_for_status()
            return response.json()['posts']
        except Exception as e:
            print(f"Error loading posts: {e}")
            return []

    def post_tweet(self, content, account_key):
        try:
            account = TWITTER_ACCOUNTS[account_key]
            auth = OAuth1Session(
                account['consumer_key'],
                client_secret=account['consumer_secret'],
                resource_owner_key=account['access_token'],
                resource_owner_secret=account['access_token_secret']
            )
            
            response = auth.post(API_URL_POST, json={'text': content})
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"Error posting tweet: {e}")
            return None

    def is_recently_posted(self, post_id, account_key):
        try:
            account_history = self.posts_history[account_key]
            if str(post_id) in account_history:
                last_posted = datetime.fromisoformat(account_history[str(post_id)])
                time_diff = datetime.now() - last_posted
                return time_diff < timedelta(hours=24)
        except Exception as e:
            print(f"Error checking recent posts: {e}")
        return False

    def post_updates(self):
        print(f"Starting post updates at {datetime.now()}")
        
        posts = self.load_posts()
        if not posts:
            print("No posts available to tweet.")
            return

        # Determine which account to use based on current time
        current_minute = datetime.now().minute
        account_key = 'account1' if current_minute % 60 < 30 else 'account2'
        print(f"Using {account_key} for this update")

        # Filter out recently posted content
        available_posts = [
            p for p in posts 
            if not self.is_recently_posted(p['id'], account_key)
        ]

        if not available_posts:
            print(f"No available posts for {account_key} at this time.")
            return

        # Select and post tweet
        post_to_tweet = random.choice(available_posts)
        content = post_to_tweet['content']
        post_id = str(post_to_tweet['id'])

        # Add posting timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        content_with_timestamp = f"{content}\n\nPosted at: {timestamp}"

        print(f"Attempting to post tweet {post_id} from {account_key}")
        response = self.post_tweet(content_with_timestamp, account_key)
        
        if response and response.status_code in (200, 201):
            print(f"Successfully posted tweet from {account_key}: {post_id}")
            self.posts_history[account_key][post_id] = datetime.now().isoformat()
            self.save_posts_history()
        else:
            print(f"Failed to post tweet from {account_key}")

def main():
    bot = TwitterBot()
    bot.post_updates()

if __name__ == "__main__":
    main()
