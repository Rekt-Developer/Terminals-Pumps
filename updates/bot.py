import os
import time
import requests
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.error import TelegramError
from typing import Optional, List, Dict, Any

# Direct API settings
COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
POST_ID = int(os.getenv("POST_ID", "6"))

# Initialize the bot globally
bot = Bot(token=BOT_TOKEN)

# Static message template with standard emojis
MESSAGE_TEMPLATE = """
⭐ *Top 4 Cryptocurrencies by Market Cap* ⭐

_Last Updated: {timestamp}_

{crypto_data}

⏰ Updates every 30 minutes
💬 Join @InvisibleSolAI for more crypto updates!
#crypto #bitcoin #ethereum #blockchain
"""

CRYPTO_ITEM_TEMPLATE = """
{rank}. *{name}* ({symbol})
💰 Price: ${price}
📊 Market Cap: {market_cap}
📈 24h: {change_24h}%
📊 7d: {change_7d}%
🏆 Rank: #{market_rank}

"""

def log_message(message: str) -> None:
    """Logs a message with timestamp."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def fetch_data(max_retries: int = 3, delay: int = 5) -> Optional[List[Dict[str, Any]]]:
    """Fetches cryptocurrency data from CoinGecko."""
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 4,
        "page": 1,
        "sparkline": False,
        "price_change_percentage": "24h,7d"
    }
    
    for attempt in range(max_retries):
        try:
            log_message("Fetching data from CoinGecko API...")
            response = requests.get(
                COINGECKO_URL,
                params=params,
                timeout=30,
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
            log_message(f"Successfully fetched data for {len(data)} tokens.")
            return data
        except requests.RequestException as e:
            log_message(f"Error fetching data (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    return None

def format_market_cap(market_cap: float) -> str:
    """Formats market cap with B/T suffix."""
    if market_cap >= 1_000_000_000_000:
        return f"${market_cap / 1_000_000_000_000:.2f}T"
    return f"${market_cap / 1_000_000_000:.2f}B"

def format_data(data: List[Dict[str, Any]]) -> str:
    """Formats data keeping static emojis intact."""
    crypto_data = ""
    for i, item in enumerate(data, 1):
        crypto_data += CRYPTO_ITEM_TEMPLATE.format(
            rank=i,
            name=item['name'],
            symbol=item['symbol'].upper(),
            price=f"{item.get('current_price', 0):,.2f}",
            market_cap=format_market_cap(item.get('market_cap', 0)),
            change_24h=f"{item.get('price_change_percentage_24h', 0):+.2f}",
            change_7d=f"{item.get('price_change_percentage_7d', 0):+.2f}",
            market_rank=item.get('market_cap_rank', 'N/A')
        )

    return MESSAGE_TEMPLATE.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
        crypto_data=crypto_data
    )

def create_inline_keyboard() -> InlineKeyboardMarkup:
    """Creates inline keyboard with preview links."""
    keyboard = [
        [
            InlineKeyboardButton(
                "📊 Charts", 
                url="https://www.coingecko.com",
                callback_data="charts"
            ),
            InlineKeyboardButton(
                "🐦 Twitter", 
                url="https://x.com/invisiblesolai",
                callback_data="twitter"
            )
        ],
        [
            InlineKeyboardButton(
                "💬 Community", 
                url="https://t.me/InvisibleSolAI",
                callback_data="community"
            ),
            InlineKeyboardButton(
                "📈 Trading", 
                url="https://www.tradingview.com",
                callback_data="trading"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def update_message_text(text: str, max_retries: int = 3) -> bool:
    """Updates only the message text, preserving existing media and markup."""
    for attempt in range(max_retries):
        try:
            bot.edit_message_text(
                chat_id=CHANNEL_ID,
                message_id=POST_ID,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=create_inline_keyboard(),
                disable_web_page_preview=True
            )
            log_message("Successfully updated message text.")
            return True
        except TelegramError as e:
            log_message(f"Error updating message (attempt {attempt + 1}/{max_retries}): {e}")
            if "message to edit not found" in str(e):
                # If message doesn't exist, send new message
                try:
                    bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=text,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=create_inline_keyboard(),
                        disable_web_page_preview=True
                    )
                    log_message("Sent new message successfully.")
                    return True
                except TelegramError as send_error:
                    log_message(f"Error sending new message: {send_error}")
            if attempt < max_retries - 1:
                time.sleep(5)
    return False

def main() -> None:
    """Main execution with text-only updates."""
    log_message("Starting InvisibleSolAI Crypto Bot...")
    
    # Verify bot token is available
    if not BOT_TOKEN:
        log_message("Error: BOT_TOKEN environment variable not set")
        return
        
    try:
        data = fetch_data()
        if not data:
            log_message("Failed to fetch data; exiting.")
            return

        formatted_text = format_data(data)
        if update_message_text(formatted_text):
            log_message("Message successfully updated.")
        else:
            log_message("Failed to update message.")
            
    except Exception as e:
        log_message(f"Fatal error in main execution: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_message("Bot stopped by user.")
    except Exception as e:
        log_message(f"Fatal error: {str(e)}")
