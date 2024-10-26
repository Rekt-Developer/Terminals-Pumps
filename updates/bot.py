import requests
import os
import time
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError

# Load secrets from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
CG_API = os.getenv("CG_API", "https://api.coingecko.com/api/v3")
POST_ID = 6  # Main post ID to modify

bot = Bot(token=BOT_TOKEN)

def fetch_data():
    """Fetches detailed token data from CoinGecko API."""
    try:
        response = requests.get(f"{CG_API}/coins/markets", params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 10,
            "page": 1,
            "sparkline": False,
            "price_change_percentage": "24h,7d,30d"
        })
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def format_market_cap(market_cap):
    """Formats market cap to readable format with B/M suffix."""
    if market_cap >= 1_000_000_000:
        return f"${market_cap / 1_000_000_000:.2f}B"
    return f"${market_cap / 1_000_000:.2f}M"

def get_trend_emoji(change):
    """Returns appropriate emoji based on price change."""
    if change >= 5:
        return "🚀"
    elif change > 0:
        return "📈"
    elif change > -5:
        return "📉"
    return "💥"

def format_data(data):
    """Formats token data for posting with enhanced details."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    formatted = f"🌟 *Top 10 Cryptocurrencies* 🌟\n\nLast Updated: {current_time}\n\n"
    
    for i, item in enumerate(data, 1):
        price_change_24h = item.get('price_change_percentage_24h', 0)
        price_change_7d = item.get('price_change_percentage_7d', 0)
        trend_emoji = get_trend_emoji(price_change_24h)
        
        formatted += (
            f"{i}. *{item['name']}* ({item['symbol'].upper()}) {trend_emoji}\n"
            f"💰 Price: ${item['current_price']:,.2f}\n"
            f"📊 Market Cap: {format_market_cap(item['market_cap'])}\n"
            f"📈 24h: {price_change_24h:+.2f}%\n"
            f"📊 7d: {price_change_7d:+.2f}%\n"
            f"💎 ATH: ${item['ath']:,.2f}\n\n"
        )
    
    formatted += "\n🔄 Updates every 30 minutes"
    return formatted

def create_inline_keyboard():
    """Creates enhanced inline keyboard with multiple buttons."""
    keyboard = [
        [
            InlineKeyboardButton("📊 Market Stats", url="https://www.coingecko.com"),
            InlineKeyboardButton("📱 Follow Us", url="https://x.com/invisiblesolai")
        ],
        [
            InlineKeyboardButton("💬 Community", url="https://t.me/InvisibleSolAI"),
            InlineKeyboardButton("📈 Trading View", url="https://www.tradingview.com")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def update_main_post(text):
    """Updates the main post with new token data."""
    try:
        bot.edit_message_text(
            chat_id=CHANNEL_ID,
            message_id=POST_ID,
            text=text,
            parse_mode="Markdown",
            reply_markup=create_inline_keyboard(),
            disable_web_page_preview=True
        )
    except TelegramError as e:
        print(f"Error updating post: {e}")

def post_new_token(token_data):
    """Posts detailed information about a newly ranked token."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    text = (
        f"🚨 *New Token Alert* 🚨\n\n"
        f"*{token_data['name']}* ({token_data['symbol'].upper()}) has entered the Top 10!\n\n"
        f"💰 Price: ${token_data['current_price']:,.2f}\n"
        f"📊 Market Cap: {format_market_cap(token_data['market_cap'])}\n"
        f"📈 24h Change: {token_data['price_change_percentage_24h']:+.2f}%\n"
        f"🔄 Volume: ${token_data['total_volume']:,.0f}\n"
        f"💎 ATH: ${token_data['ath']:,.2f}\n"
        f"📅 Time: {current_time}"
    )
    
    try:
        bot.send_message(
            chat_id=CHANNEL_ID,
            text=text,
            parse_mode="Markdown",
            reply_markup=create_inline_keyboard(),
            disable_web_page_preview=True
        )
    except TelegramError as e:
        print(f"Error posting new token: {e}")

def main():
    print("Starting CoinGecko Telegram Bot...")
    last_update = None
    known_tokens = set()
    
    while True:
        try:
            current_time = datetime.now()
            data = fetch_data()
            
            if not data:
                print("Failed to fetch data, retrying in 5 minutes...")
                time.sleep(300)
                continue
                
            # Update main post every hour
            if not last_update or (current_time - last_update).seconds >= 3600:
                formatted_text = format_data(data)
                update_main_post(formatted_text)
                last_update = current_time
                print(f"Main post updated at {current_time}")
                
            # Check for new tokens
            current_tokens = {token['id'] for token in data}
            new_tokens = current_tokens - known_tokens
            
            for token in data:
                if token['id'] in new_tokens:
                    post_new_token(token)
                    print(f"New token alert posted: {token['name']}")
            
            known_tokens = current_tokens
            time.sleep(1800)  # Wait for 30 minutes
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(300)  # Wait 5 minutes before retrying

if __name__ == "__main__":
    main()
