import requests
import random
import os
import json
from datetime import datetime, timedelta
from requests_oauthlib import OAuth1Session

# Twitter API configurations
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

# CryptoCompare API configurations
API_KEY = "1048c9d7ef0df6358f984e6be9466c9b5d83eb5f26a0a57741be7f3f7bd6eb03"
NEWS_URL = "https://min-api.cryptocompare.com/data/v2/news/"
SIGNAL_URL = "https://min-api.cryptocompare.com/data/tradingsignals/intotheblock/latest"

# Emoji mappings for trading sentiment
SENTIMENT_EMOJIS = {
    'bullish': '📈🚀',
    'bearish': '📉🔻',
    'neutral': '🤔'
}

class TwitterBot:
    def __init__(self):
        self.posts_history = self.load_posts_history()

    def load_posts_history(self):
        """Load post history from a file."""
        try:
            if os.path.exists('post_history.json'):
                with open('post_history.json', 'r') as file:
                    return json.load(file)
        except Exception as e:
            print(f"Error loading post history: {e}")
        return {'account1': {}, 'account2': {}}

    def save_posts_history(self):
        """Save updated post history to a file."""
        try:
            with open('post_history.json', 'w') as file:
                json.dump(self.posts_history, file, indent=2)
            print("Post history saved successfully.")
        except Exception as e:
            print(f"Error saving post history: {e}")

    def fetch_news(self):
        """Fetch latest news articles."""
        try:
            params = {'api_key': API_KEY, 'sortOrder': 'latest'}
            response = requests.get(NEWS_URL, params=params)
            response.raise_for_status()
            news_data = response.json().get('Data', [])
            return news_data
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []

    def fetch_trading_signal(self, symbol):
        """Fetch the latest trading signal for a given symbol."""
        try:
            url = f"{SIGNAL_URL}?fsym={symbol}&api_key={API_KEY}"
            response = requests.get(url)
            response.raise_for_status()
            signal_data = response.json().get('Data', {})
            return signal_data
        except Exception as e:
            print(f"Error fetching trading signal: {e}")
            return {}

    def post_tweet(self, content, account_key, image_url=None):
        """Post a tweet with optional media."""
        try:
            account = TWITTER_ACCOUNTS[account_key]
            auth = OAuth1Session(
                account['consumer_key'],
                client_secret=account['consumer_secret'],
                resource_owner_key=account['access_token'],
                resource_owner_secret=account['access_token_secret']
            )

            payload = {'text': content}
            if image_url:
                # Upload image URL to Twitter and get media ID
                media_id = self.upload_media_from_url(image_url, auth)
                if media_id:
                    payload['media'] = {'media_ids': [media_id]}

            response = auth.post("https://api.twitter.com/2/tweets", json=payload)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"Error posting tweet: {e}")
            return None

    def upload_media_from_url(self, image_url, auth):
        """Upload media to Twitter from a URL."""
        try:
            image_data = requests.get(image_url).content
            response = auth.post(
                'https://upload.twitter.com/1.1/media/upload.json',
                files={'media': image_data}
            )
            response.raise_for_status()
            return response.json().get('media_id_string')
        except Exception as e:
            print(f"Error uploading media from URL: {e}")
            return None

    def is_recently_posted(self, post_id, account_key):
        """Check if a post has been recently posted to avoid duplicates."""
        try:
            account_history = self.posts_history.get(account_key, {})
            if str(post_id) in account_history:
                last_posted = datetime.fromisoformat(account_history[str(post_id)])
                return datetime.now() - last_posted < timedelta(hours=24)
        except Exception as e:
            print(f"Error checking recent posts: {e}")
        return False

    def generate_hashtags(self, text, symbol=None):
        """Generate hashtags based on the given text."""
        keywords = [word for word in text.split() if len(word) > 3]
        base_hashtags = random.sample(keywords, min(3, len(keywords)))
        if symbol:
            base_hashtags.append(symbol)
        return ' '.join([f"#{word}" for word in base_hashtags])

    def post_updates(self):
        """Post updates to Twitter."""
        print("Starting post updates...")

        # Get latest news
        news_posts = self.fetch_news()
        if not news_posts:
            print("No news to post.")
            return

        # Determine account to use
        current_minute = datetime.now().minute
        account_key = 'account1' if current_minute % 60 < 30 else 'account2'
        print(f"Using {account_key} for updates.")

        # Post the latest news
        for news in news_posts[:5]:  # Limit to 5 news posts per update
            news_id = news.get('id')
            title = news.get('title')
            image_url = news.get('imageurl')
            if not title or self.is_recently_posted(news_id, account_key):
                continue

            hashtags = self.generate_hashtags(title)
            content = f"{title}\n\n{hashtags}"
            response = self.post_tweet(content, account_key, image_url)
            if response and response.status_code in (200, 201):
                print(f"Tweeted news: {title}")
                self.posts_history[account_key][news_id] = datetime.now().isoformat()
                self.save_posts_history()

        # Post trading signals for BTC and ETH
        for symbol in ['BTC', 'ETH']:
            signal = self.fetch_trading_signal(symbol)
            if not signal:
                continue

            sentiment = signal.get('inOutVar', {}).get('sentiment', 'neutral')
            emoji = SENTIMENT_EMOJIS.get(sentiment, '🤔')
            score = signal.get('inOutVar', {}).get('score', 'N/A')

            signal_content = (
                f"🚨 {symbol} Trading Signal {emoji}\n"
                f"Sentiment: {sentiment.capitalize()}\n"
                f"Score: {score}\n"
                f"#Crypto #Trading #{symbol}"
            )
            response = self.post_tweet(signal_content, account_key)
            if response and response.status_code in (200, 201):
                print(f"Tweeted trading signal for {symbol}.")

def main():
    bot = TwitterBot()
    bot.post_updates()

if __name__ == "__main__":
    main()
