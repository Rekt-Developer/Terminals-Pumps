import os
import time
import requests
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.error import TelegramError
from typing import Optional, List, Dict, Any

# Direct API settings
COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
POST_ID = int(os.getenv("POST_ID", "6"))  # Default post ID for main channel update

# Validate necessary environment variables
if not all([BOT_TOKEN, CHANNEL_ID]):
    raise ValueError("Environment variables BOT_TOKEN and CHANNEL_ID must be set")

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

def format_data(data: List[Dict[str, Any]]) -> str:
    """Formats top 4 tokens data for posting with premium animated emojis."""
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

    formatted += (
        "\n🔄 Updates every 30 minutes\n"
        "💬 Join @InvisibleSolAI for more crypto updates!"
    )
    return formatted

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

def send_or_update_main_post(text: str, image_url: str, max_retries: int = 3) -> bool:
    """Sends or updates the main post with token data and attaches image."""
    for attempt in range(max_retries):
        try:
            # If updating fails (post not found), send a new media post
            log_message("Attempting to update the main post with image...")
            bot.edit_message_media(
                chat_id=CHANNEL_ID,
                message_id=POST_ID,
                media=InputMediaPhoto(media=image_url, caption=text, parse_mode="Markdown"),
                reply_markup=create_inline_keyboard()
            )
            log_message("Main post updated successfully.")
            return True
        except TelegramError as e:
            log_message(f"Error updating post (attempt {attempt + 1}): {e}")
            if "message to edit not found" in str(e):
                log_message("Message not found; sending new message with media...")
                bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=image_url,
                    caption=text,
                    parse_mode="Markdown",
                    reply_markup=create_inline_keyboard(),
                )
                return True
            elif "Timed out" in str(e):
                log_message("Retrying due to timeout...")
                time.sleep(5)
            else:
                break
    log_message("Failed to update the main post after retries.")
    return False

def main() -> None:
    """Main execution for bot: fetches, formats, and updates post with media."""
    log_message("Starting InvisibleSolAI Crypto Bot...")
    
    # Fetch top 4 token data
    data = fetch_data()
    if not data:
        log_message("Failed to fetch data; exiting.")
        return

    # Format and attempt to update the main post with media
    formatted_text = format_data(data)
    image_url = "https://static.news.bitcoin.com/wp-content/uploads/2019/01/bj2rNGhZ-ezgif-2-e18c3be26209.gif"
    if send_or_update_main_post(formatted_text, image_url):
        log_message("Main post with image updated successfully on first attempt.")
    else:
        log_message("Failed to update main post on first attempt.")
    
    log_message("Bot execution completed. Exiting.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_message("Bot stopped by user.")
    except Exception as e:
        log_message(f"Fatal error: {e}")
