import os
import time
import requests
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.error import TelegramError
from typing import Optional, List, Dict, Any
import schedule  # Make sure to install 'schedule' package for the scheduler

# Direct API settings
COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
POST_ID = int(os.getenv("POST_ID", "6"))  # Default post ID for main channel update

# Validate necessary environment variables
if not all([BOT_TOKEN, CHANNEL_ID, POST_ID]):
    raise ValueError("Environment variables BOT_TOKEN, CHANNEL_ID, and POST_ID must be set")

# Initialize Telegram bot
bot = Bot(token=BOT_TOKEN)

def log_message(message: str) -> None:
    """Logs a message with timestamp."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def fetch_data(max_retries: int = 3, delay: int = 5) -> Optional[List[Dict[str, Any]]]:
    """Fetches top 4 cryptocurrency data from CoinGecko with retries on failure."""
    for attempt in range(max_retries):
        try:
            log_message("Fetching top 4 cryptocurrencies data from CoinGecko API...")
            response = requests.get(
                COINGECKO_URL,
                params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": 4,  # Limit to top 4 tokens
                    "page": 1,
                    "sparkline": True,
                    "price_change_percentage": "24h,7d,30d"
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            log_message(f"Successfully fetched data for {len(data)} tokens.")
            return data
        except requests.RequestException as e:
            log_message(f"Error fetching data (attempt {attempt + 1}): {e}")
            time.sleep(delay)
    log_message("All retries failed; could not fetch data.")
    return None

def format_market_cap(market_cap: float) -> str:
    """Formats market cap with B/M suffix for readability."""
    if market_cap >= 1_000_000_000:
        return f"${market_cap / 1_000_000_000:.2f}B"
    return f"${market_cap / 1_000_000:.2f}M"

def get_trend_emoji(change: float) -> str:
    """Returns an emoji based on price trend using animated emojis."""
    if change >= 5:
        return "🚀"
    elif change > 0:
        return "📈"
    elif change > -5:
        return "📉"
    return "💥"

def format_main_post(data: List[Dict[str, Any]]) -> str:
    """Formats detailed top 4 tokens data for the main pinned post with emojis."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    formatted = (
        f"🌟 *Top 4 Cryptocurrencies by Market Cap* 🌟\n\n"
        f"_Last Updated: {current_time}_\n\n"
    )
    for i, item in enumerate(data, 1):
        price_change_24h = item.get("price_change_percentage_24h", 0) or 0
        price_change_7d = item.get("price_change_percentage_7d", 0) or 0
        trend_emoji = get_trend_emoji(price_change_24h)
        
        formatted += (
            f"{i}. *{item['name']}* ({item['symbol'].upper()}) {trend_emoji}\n"
            f"💰 Price: ${item.get('current_price', 0):,.2f}\n"
            f"📊 Market Cap: {format_market_cap(item.get('market_cap', 0))}\n"
            f"📈 24h Change: {price_change_24h:+.2f}%\n"
            f"📊 7d Change: {price_change_7d:+.2f}%\n"
            f"🏆 Rank: #{item.get('market_cap_rank', 'N/A')}\n\n"
        )
    formatted += "\n🔄 Updates every 30 minutes\n💬 Join @InvisibleSolAI for more crypto updates!"
    return formatted

def format_short_post(data: List[Dict[str, Any]]) -> str:
    """Formats a brief update with top 2 cryptocurrencies for hourly posts."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    formatted = f"🕒 *Hourly Crypto Update* - {current_time} 🕒\n\n"
    
    for i, item in enumerate(data[:2], 1):  # Show only top 2 in short update
        price_change_24h = item.get("price_change_percentage_24h", 0) or 0
        trend_emoji = get_trend_emoji(price_change_24h)
        
        formatted += (
            f"{i}. *{item['name']}* ({item['symbol'].upper()}) {trend_emoji}\n"
            f"💰 ${item.get('current_price', 0):,.2f} | 24h: {price_change_24h:+.2f}%\n\n"
        )
    return formatted.strip()

def create_inline_keyboard() -> InlineKeyboardMarkup:
    """Creates a custom inline keyboard with relevant links."""
    keyboard = [
        [
            InlineKeyboardButton("📊 Market Stats", url="https://www.coingecko.com"),
            InlineKeyboardButton("📱 Follow Us", url="https://x.com/invisiblesolai"),
        ],
        [
            InlineKeyboardButton("💬 Community", url="https://t.me/InvisibleSolAI"),
            InlineKeyboardButton("📈 Trading View", url="https://www.tradingview.com"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def send_main_post(image_url: str) -> None:
    """Posts or updates the main pinned post with detailed token data."""
    data = fetch_data()
    if not data:
        log_message("Failed to fetch data for main post.")
        return
    
    text = format_main_post(data)
    try:
        bot.edit_message_media(
            chat_id=CHANNEL_ID,
            message_id=POST_ID,
            media=InputMediaPhoto(media=image_url, caption=text, parse_mode="Markdown"),
            reply_markup=create_inline_keyboard()
        )
        log_message("Main pinned post updated successfully.")
    except TelegramError as e:
        log_message(f"Error updating main post: {e}")

def post_hourly_update(image_url: str) -> None:
    """Posts a short, hourly update with top 2 cryptocurrencies."""
    data = fetch_data()
    if not data:
        log_message("Failed to fetch data for hourly update.")
        return
    
    text = format_short_post(data)
    try:
        bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=image_url,
            caption=text,
            parse_mode="Markdown",
            reply_markup=create_inline_keyboard()
        )
        log_message("Hourly update posted successfully.")
    except TelegramError as e:
        log_message(f"Error posting hourly update: {e}")

def main() -> None:
    """Main scheduler loop to run updates."""
    log_message("Starting InvisibleSolAI Crypto Bot...")
    
    image_url = "https://static.news.bitcoin.com/wp-content/uploads/2019/01/bj2rNGhZ-ezgif-2-e18c3be26209.gif"
    
    # Schedule tasks
    schedule.every().hour.at(":00").do(post_hourly_update, image_url=image_url)  # Post short update every hour
    schedule.every().hour.at(":30").do(send_main_post, image_url=image_url)      # Update main pinned post every 30 minutes

    # Continuous run to check for pending scheduled tasks
    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_message("Bot stopped by user.")
    except Exception as e:
        log_message(f"Fatal error: {e}")

