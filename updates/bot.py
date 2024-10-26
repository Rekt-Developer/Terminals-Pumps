import os
import time
import requests
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from typing import Optional, List, Dict, Any

# Load secrets from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
POST_ID = int(os.getenv("POST_ID", "6"))  # Default post ID is 6 if not provided
COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"

# Ensure necessary environment variables are set
if not all([BOT_TOKEN, CHANNEL_ID]):
    raise ValueError("Environment variables BOT_TOKEN and CHANNEL_ID must be set")

bot = Bot(token=BOT_TOKEN)

def log_message(message: str) -> None:
    """Logs a message with a timestamp."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def fetch_data(max_retries: int = 3, delay: int = 5) -> Optional[List[Dict[str, Any]]]:
    """Fetches token data from CoinGecko API with retry logic on failure."""
    for attempt in range(max_retries):
        try:
            log_message("Fetching data from CoinGecko API...")
            response = requests.get(
                COINGECKO_URL,
                params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": 300,
                    "page": 1,
                    "sparkline": True,
                    "price_change_percentage": "24h,7d,30d"
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            log_message(f"Successfully fetched data for {len(data)} tokens")
            return data[:300]  # Limit to 300 tokens
        except requests.RequestException as e:
            log_message(f"Error fetching data (attempt {attempt + 1}): {e}")
            time.sleep(delay)
    log_message("All retries failed; could not fetch data.")
    return None

def format_market_cap(market_cap: float) -> str:
    """Formats the market cap with B/M suffix."""
    if market_cap >= 1_000_000_000:
        return f"${market_cap / 1_000_000_000:.2f}B"
    return f"${market_cap / 1_000_000:.2f}M"

def get_trend_emoji(change: float) -> str:
    """Returns trend emoji based on price change."""
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
    formatted = f"🌟 *Top Cryptocurrencies by Market Cap* 🌟\n\n_Last Updated: {current_time}_\n\n"
    
    for i, item in enumerate(data[:20], 1):
        price_change_24h = item.get("price_change_percentage_24h", 0) or 0
        price_change_7d = item.get("price_change_percentage_7d", 0) or 0
        sparkline = item.get("sparkline_in_7d", {}).get("price", [])
        trend_emoji = get_trend_emoji(price_change_24h)

        last_price = sparkline[-1] if sparkline else item.get("current_price", 0)
        
        formatted += (
            f"{i}. *{item['name']}* ({item['symbol'].upper()}) {trend_emoji}\n"
            f"💰 Price: ${last_price:,.2f}\n"
            f"📊 Market Cap: {format_market_cap(item.get('market_cap', 0))}\n"
            f"📈 24h Change: {price_change_24h:+.2f}%\n"
            f"📊 7d Change: {price_change_7d:+.2f}%\n"
            f"🏆 Rank: #{item.get('market_cap_rank', 'N/A')}\n\n"
        )

    formatted += (
        f"\n📊 Tracking {len(data)} top cryptocurrencies\n"
        f"🔄 Auto-updates every 30 minutes\n💬 Join @InvisibleSolAI for more updates!"
    )
    return formatted

def create_inline_keyboard() -> InlineKeyboardMarkup:
    """Creates an inline keyboard with custom buttons for external links."""
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

def update_main_post(text: str) -> bool:
    """Updates the main post in the Telegram channel with new token data."""
    log_message("Updating main post...")
    try:
        bot.edit_message_text(
            chat_id=CHANNEL_ID,
            message_id=POST_ID,
            text=text,
            parse_mode="Markdown",
            reply_markup=create_inline_keyboard(),
            disable_web_page_preview=True,
        )
        log_message("Main post updated successfully.")
        return True
    except TelegramError as e:
        log_message(f"Error updating post: {e}")
        return False

def main() -> None:
    """Main function to fetch data, format it, and update the Telegram post."""
    log_message("Starting CoinGecko Telegram Bot - Single Run Mode...")
    
    data = fetch_data()
    if not data:
        log_message("Failed to fetch data on initial attempt. Exiting.")
        return
    
    formatted_text = format_data(data)
    if update_main_post(formatted_text):
        log_message("Main post updated successfully on initial run.")
    else:
        log_message("Failed to update main post on initial run.")
    
    log_message("Bot execution completed. Exiting.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_message("Bot stopped by user.")
    except Exception as e:
        log_message(f"Fatal error: {e}")
