from flask import Flask
from requests_oauthlib import OAuth1Session
import requests
import random
import os
import json
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', '42ONMdu8fVecRgtv6WwZo-70K8frkHOBW4WJbF9JkcJI3BP82q')

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
POSTS_HISTORY_FILE = 'posted_history.json'

class TwitterBot:
    def __init__(self):
        self.posts_history = self.load_posts_history()
        
    def load_posts_history(self):
        if os.path.exists(POSTS_HISTORY_FILE):
            with open(POSTS_HISTORY_FILE, 'r') as file:
                return json.load(file)
        return {'account1': {}, 'account2': {}}

    def save_posts_history(self):
        with open(POSTS_HISTORY_FILE, 'w') as file:
            json.dump(self.posts_history, file)

    def load_posts(self):
        response = requests.get('https://raw.githubusercontent.com/likhonisaac/Terminals-Pumps/refs/heads/main/post/post.json')
        if response.status_code == 200:
            data = response.json()
            return data['posts']
        return []

    def post_tweet(self, content, account_key):
        account = TWITTER_ACCOUNTS[account_key]
        auth = OAuth1Session(
            account['consumer_key'],
            client_secret=account['consumer_secret'],
            resource_owner_key=account['access_token'],
            resource_owner_secret=account['access_token_secret']
        )
        
        response = auth.post(API_URL_POST, json={'text': content})
        return response

    def is_recently_posted(self, post_id, account_key):
        account_history = self.posts_history[account_key]
        if str(post_id) in account_history:
            last_posted = datetime.fromisoformat(account_history[str(post_id)])
            time_diff = datetime.now() - last_posted
            return time_diff < timedelta(hours=24)  # Prevent reposting within 24 hours
        return False

    def schedule_post(self):
        posts = self.load_posts()
        if not posts:
            print("No posts available to tweet.")
            return

        # Alternate between accounts
        current_time = datetime.now()
        account_key = 'account1' if current_time.minute % 60 < 30 else 'account2'
        
        # Filter out recently posted content
        available_posts = [
            p for p in posts 
            if not self.is_recently_posted(p['id'], account_key)
        ]

        if not available_posts:
            print(f"No available posts for {account_key} at this time.")
            return

        post_to_tweet = random.choice(available_posts)
        content = post_to_tweet['content']
        post_id = str(post_to_tweet['id'])

        # Add posting timestamp to the content
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        content_with_timestamp = f"{content}\n\nPosted at: {timestamp}"

        response = self.post_tweet(content_with_timestamp, account_key)
        
        if response.status_code == 201:
            print(f"Posted successfully from {account_key}: {content}")
            self.posts_history[account_key][post_id] = datetime.now().isoformat()
            self.save_posts_history()
        else:
            print(f"Failed to post tweet from {account_key}: {response.status_code} - {response.text}")

# Initialize the Twitter bot
twitter_bot = TwitterBot()

# Set up the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(twitter_bot.schedule_post, 'interval', minutes=30)
scheduler.start()

@app.route('/')
def index():
    return "Twitter Bot is running with dual account support!"

if __name__ == "__main__":
    app.run(debug=True)
