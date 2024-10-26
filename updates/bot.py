import os
import time
import requests
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from typing import Optional, Set, Dict, Any, List

# Load secrets from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
CG_API = os.getenv("CG_API", "https://api.coingecko.com/api/v3")
POST_ID = 6  # Main post ID to modify

# Validate environment variables
if not all([BOT_TOKEN, CHANNEL_ID]):
    raise ValueError("Required environment variables BOT_TOKEN and CHANNEL_ID must be set")

bot = Bot(token=BOT_TOKEN)

def log_message(message: str) -> None:
    """Print timestamp with log message"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] {message}")

def fetch_data() -> Optional[List[Dict[str, Any]]]:
    """Fetches detailed token data from CoinGecko API."""
    log_message("Fetching data from CoinGecko API...")
    try:
        response = requests.get(
            f"{CG_API}/coins/markets",
            params={
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": 10,
                "page": 1,
                "sparkline": False,
                "price_change_percentage": "24h,7d,30d"
            },
            timeout=30  # Add timeout to prevent hanging
        )
        response.raise_for_status()
        data = response.json()
        log_message(f"Successfully fetched data for {len(data)} tokens")
        return data
    except requests.RequestException as e:
        log_message(f"Error fetching data: {e}")
        return None

def format_market_cap(market_cap: float) -> str:
    """Formats market cap to readable format with B/M suffix."""
    if market_cap >= 1_000_000_000:
        return f"${market_cap / 1_000_000_000:.2f}B"
    return f"${market_cap / 1_000_000:.2f}M"

def get_trend_emoji(change: float) -> str:
    """Returns appropriate emoji based on price change."""
    if change >= 5:
        return "🚀"
    elif change > 0:
        return "📈"
    elif change > -5:
        return "📉"
    return "💥"

def format_data(data: List[Dict[str, Any]]) -> str:
    """Formats token data for posting with enhanced details."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    formatted = f"🌟 *Top 10 Cryptocurrencies* 🌟\n\nLast Updated: {current_time}\n\n"
    
    for i, item in enumerate(data, 1):
        price_change_24h = item.get('price_change_percentage_24h', 0) or 0
        price_change_7d = item.get('price_change_percentage_7d', 0) or 0
        trend_emoji = get_trend_emoji(price_change_24h)
        
        formatted += (
            f"{i}. *{item['name']}* ({item['symbol'].upper()}) {trend_emoji}\n"
            f"💰 Price: ${item.get('current_price', 0):,.2f}\n"
            f"📊 Market Cap: {format_market_cap(item.get('market_cap', 0))}\n"
            f"📈 24h: {price_change_24h:+.2f}%\n"
            f"📊 7d: {price_change_7d:+.2f}%\n"
            f"💎 ATH: ${item.get('ath', 0):,.2f}\n\n"
        )
    
    formatted += "\n🔄 Auto-updates every 30 minutes\n💬 Join @InvisibleSolAI for more updates!"
    return formatted

def create_inline_keyboard() -> InlineKeyboardMarkup:
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

def update_main_post(text: str) -> bool:
    """Updates the main post with new token data."""
    log_message("Updating main post...")
    try:
        bot.edit_message_text(
            chat_id=CHANNEL_ID,
            message_id=POST_ID,
            text=text,
            parse_mode="Markdown",
            reply_markup=create_inline_keyboard(),
            disable_web_page_preview=True
        )
        log_message("Main post updated successfully")
        return True
    except TelegramError as e:
        log_message(f"Error updating post: {e}")
        return False

def post_new_token(token_data: Dict[str, Any]) -> None:
    """Posts detailed information about a newly ranked token."""
    log_message(f"Posting alert for new token: {token_data['name']}")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    text = (
        f"🚨 *New Token Alert* 🚨\n\n"
        f"*{token_data['name']}* ({token_data['symbol'].upper()}) has entered the Top 10!\n\n"
        f"💰 Price: ${token_data.get('current_price', 0):,.2f}\n"
        f"📊 Market Cap: {format_market_cap(token_data.get('market_cap', 0))}\n"
        f"📈 24h Change: {token_data.get('price_change_percentage_24h', 0):+.2f}%\n"
        f"🔄 Volume: ${token_data.get('total_volume', 0):,.0f}\n"
        f"💎 ATH: ${token_data.get('ath', 0):,.2f}\n"
        f"📅 Time: {current_time}\n\n"
        f"💬 Join @InvisibleSolAI for more updates!"
    )
    
    try:
        bot.send_message(
            chat_id=CHANNEL_ID,
            text=text,
            parse_mode="Markdown",
            reply_markup=create_inline_keyboard(),
            disable_web_page_preview=True
        )
        log_message(f"New token alert posted successfully for {token_data['name']}")
    except TelegramError as e:
        log_message(f"Error posting new token: {e}")

def main() -> None:
    log_message("Starting CoinGecko Telegram Bot...")
    
    # Add error handling for initial connection
    retry_count = 0
    max_retries = 5
    initial_data = None
    
    while retry_count < max_retries and not initial_data:
        initial_data = fetch_data()
        if not initial_data:
            retry_count += 1
            wait_time = min(300 * retry_count, 1800)  # Exponential backoff, max 30 minutes
            log_message(f"Retry {retry_count}/{max_retries} in {wait_time} seconds...")
            time.sleep(wait_time)
    
    if not initial_data:
        log_message("Failed to fetch initial data after maximum retries. Exiting.")
        return

    formatted_text = format_data(initial_data)
    if update_main_post(formatted_text):
        log_message("Initial update completed successfully")
    else:
        log_message("Initial update failed")

    known_tokens = {token['id'] for token in initial_data}
    last_update = datetime.now()
    
    log_message("Entering main update loop...")
    while True:
        try:
            current_time = datetime.now()
            data = fetch_data()
            
            if not data:
                log_message("Failed to fetch data, retrying in 5 minutes...")
                time.sleep(300)
                continue
            
            # Always update the main post first
            formatted_text = format_data(data)
            update_success = update_main_post(formatted_text)
            if update_success:
                last_update = current_time
            
            # Check for new tokens
            current_tokens = {token['id'] for token in data}
            new_tokens = current_tokens - known_tokens
            
            for token in data:
                if token['id'] in new_tokens:
                    post_new_token(token)
            
            known_tokens = current_tokens
            log_message("Waiting 30 minutes until next update...")
            time.sleep(1800)  # Wait for 30 minutes
            
        except Exception as e:
            log_message(f"Error in main loop: {e}")
            time.sleep(300)  # Wait 5 minutes before retrying

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_message("Bot stopped by user")
    except Exception as e:
        log_message(f"Fatal error: {e}")
