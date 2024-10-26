import requests
import random
import os
import json
from datetime import datetime, timedelta
from requests_oauthlib import OAuth1Session
import tempfile
from urllib.parse import urlparse

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

# API endpoints
API_URL_POST = 'https://api.twitter.com/2/tweets'
API_MEDIA_UPLOAD = 'https://upload.twitter.com/1.1/media/upload.json'

# Repository information
REPO_OWNER = 'likhonisaac'
REPO_NAME = 'Terminals-Pumps'
HISTORY_FILE = 'post_history.json'
IMAGES_FOLDER = 'images'  # Local folder containing images
USED_IMAGES_FILE = 'used_images.json'  # Track used images

class TwitterBot:
    def __init__(self):
        self.posts_history = self.load_posts_history()
        self.used_images = self.load_used_images()
        
    def load_posts_history(self):
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r') as file:
                    return json.load(file)
        except Exception as e:
            print(f"Error loading history: {e}")
        return {'account1': {}, 'account2': {}}

    def load_used_images(self):
        """Load the history of used images"""
        try:
            if os.path.exists(USED_IMAGES_FILE):
                with open(USED_IMAGES_FILE, 'r') as file:
                    return json.load(file)
        except Exception as e:
            print(f"Error loading used images history: {e}")
        return []

    def save_used_images(self):
        """Save the updated used images list"""
        try:
            with open(USED_IMAGES_FILE, 'w') as file:
                json.dump(self.used_images, file, indent=2)
            print(f"Successfully saved used images history to {USED_IMAGES_FILE}")
        except Exception as e:
            print(f"Error saving used images history: {e}")

    def get_available_images(self):
        """Get list of available images from the folder"""
        try:
            if not os.path.exists(IMAGES_FOLDER):
                os.makedirs(IMAGES_FOLDER)
                print(f"Created images folder: {IMAGES_FOLDER}")
                return []

            all_images = [f for f in os.listdir(IMAGES_FOLDER) 
                         if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
            
            # Filter out used images
            available_images = [img for img in all_images if img not in self.used_images]
            
            # If all images have been used, reset the history
            if not available_images:
                print("All images have been used, resetting history")
                self.used_images = []
                self.save_used_images()
                available_images = all_images
            
            return available_images
        except Exception as e:
            print(f"Error getting available images: {e}")
            return []

    def get_random_image(self):
        """Select a random unused image from the folder"""
        available_images = self.get_available_images()
        if not available_images:
            print("No images available in the folder")
            return None
            
        selected_image = random.choice(available_images)
        image_path = os.path.join(IMAGES_FOLDER, selected_image)
        
        # Mark image as used
        self.used_images.append(selected_image)
        self.save_used_images()
        
        print(f"Selected image: {selected_image}")
        return image_path

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

    def upload_media(self, image_path, auth):
        """Upload media to Twitter and return the media ID."""
        try:
            # Read the image file
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
            
            # Upload the image
            response = auth.post(API_MEDIA_UPLOAD, files={'media': image_data})
            response.raise_for_status()
            
            media_id = response.json()['media_id_string']
            print(f"Successfully uploaded media with ID: {media_id}")
            return media_id
        except Exception as e:
            print(f"Error uploading media: {e}")
            return None

    def post_tweet(self, content, account_key, media_id=None):
        try:
            account = TWITTER_ACCOUNTS[account_key]
            auth = OAuth1Session(
                account['consumer_key'],
                client_secret=account['consumer_secret'],
                resource_owner_key=account['access_token'],
                resource_owner_secret=account['access_token_secret']
            )
            
            # Prepare tweet payload
            payload = {'text': content}
            if media_id:
                payload['media'] = {'media_ids': [media_id]}
            
            response = auth.post(API_URL_POST, json=payload)
            response.raise_for_status()
            return response, auth
        except Exception as e:
            print(f"Error posting tweet: {e}")
            return None, None

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

        # Get random image from folder
        image_path = self.get_random_image()
        if not image_path:
            print("Failed to get image, proceeding without media")

        # Select and post tweet
        post_to_tweet = random.choice(available_posts)
        content = post_to_tweet['content']
        post_id = str(post_to_tweet['id'])

        # Add posting timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        content_with_timestamp = f"{content}\n\nPosted at: {timestamp}"

        print(f"Attempting to post tweet {post_id} from {account_key}")
        
        media_id = None
        if image_path:
            # First create OAuth session for media upload
            account = TWITTER_ACCOUNTS[account_key]
            auth = OAuth1Session(
                account['consumer_key'],
                client_secret=account['consumer_secret'],
                resource_owner_key=account['access_token'],
                resource_owner_secret=account['access_token_secret']
            )
            media_id = self.upload_media(image_path, auth)

        response, _ = self.post_tweet(content_with_timestamp, account_key, media_id)
        
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
