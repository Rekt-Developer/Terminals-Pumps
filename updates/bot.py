import requests
import os
import time
from telegram import Bot
from telegram.error import TelegramError

# Load secrets from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
CG_API = os.getenv("CG_API")

bot = Bot(token=BOT_TOKEN)
POST_ID = 6  # Main post ID to modify every 30 minutes

def fetch_data():
    """Fetches token data from CoinGecko API."""
    try:
        response = requests.get(f"{CG_API}/coins/markets", params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 10,  # Fetch top 10 tokens
            "page": 1,
            "sparkline": False
        })
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def format_data(data):
    """Formats token data for posting."""
    formatted = ""
    for item in data:
        emoji = "🔥" if item['price_change_percentage_24h'] > 0 else "❄️"
        formatted += f"🥇 {item['name']} ❕ {item['market_cap']} ❕ {item['price_change_percentage_24h']}% {emoji}\n"
    return formatted

def update_main_post(text):
    """Updates the main post with new token data."""
    try:
        bot.edit_message_text(
            chat_id=CHANNEL_ID,
            message_id=POST_ID,
            text=text,
            parse_mode="Markdown",
            reply_markup={"inline_keyboard": [[{"text": "Trending", "url": "https://x.com/invisiblesolai"}]]}
        )
    except TelegramError as e:
        print(f"Error updating post: {e}")

def post_new_token(token_data):
    """Posts about a newly ranked token if needed."""
    text = f"🔥 New Token Alert!\n\n{format_data([token_data])}"
    try:
        bot.send_message(
            chat_id=CHANNEL_ID,
            text=text,
            parse_mode="Markdown",
            reply_markup={"inline_keyboard": [[{"text": "Trending", "url": "https://x.com/invisiblesolai"}]]}
        )
    except TelegramError as e:
        print(f"Error posting new token: {e}")

def main():
    # Fetch initial data and post it
    data = fetch_data()
    if not data:
        return

    formatted_text = format_data(data)
    update_main_post(formatted_text)

    # Check for changes every 30 minutes
    while True:
        time.sleep(1800)  # Wait for 30 minutes
        new_data = fetch_data()
        if not new_data:
            continue

        new_formatted_text = format_data(new_data)
        
        # Update the main post if data changed
        if new_formatted_text != formatted_text:
            update_main_post(new_formatted_text)
            formatted_text = new_formatted_text

        # Check for new tokens and post if they enter the top 10
        for token in new_data:
            if token not in data:
                post_new_token(token)

if __name__ == "__main__":
    main()
