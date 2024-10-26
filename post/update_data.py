import requests
import json
import os
import logging
from datetime import datetime
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# CoinGecko API URLs
CRYPTO_API_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true"
TRENDING_API_URL = "https://api.coingecko.com/api/v3/search/trending"

# File paths
POSTS_FILE = 'post/post.json'
MD_FILE = 'post/data.md'  # Adjusted to save markdown file as .md

def load_json(file_path):
    try:
        if not os.path.exists(file_path):
            logging.error(f"File does not exist: {file_path}")
            sys.exit(1)

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Failed to load JSON file: {e}")
        sys.exit(1)

def save_json(data, file_path):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logging.info(f"JSON data saved to {file_path}")
    except Exception as e:
        logging.error(f"Failed to save JSON file: {e}")
        sys.exit(1)

def fix_duplicate_ids(data):
    unique_id = 1
    seen_ids = set()
    for post in data.get("posts", []):
        if post["id"] in seen_ids:
            logging.info(f"Duplicate ID {post['id']} found. Assigning new ID: {unique_id}")
            post["id"] = unique_id
            unique_id += 1
        seen_ids.add(post["id"])
    logging.info("Duplicate IDs fixed")
    return data

def fetch_crypto_data():
    try:
        response = requests.get(CRYPTO_API_URL)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch cryptocurrency data: {e}")
        return None

def fetch_trending_data():
    try:
        response = requests.get(TRENDING_API_URL)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch trending data: {e}")
        return None

def create_markdown(crypto_data, trending_data, posts):
    markdown_content = "# Cryptocurrency Data\n\n"
    markdown_content += f"**Last updated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"

    markdown_content += "## Live Prices\n"
    if crypto_data:
        bitcoin = crypto_data.get("bitcoin", {})
        ethereum = crypto_data.get("ethereum", {})

        markdown_content += f"- **Bitcoin (BTC)**: ${bitcoin.get('usd', 'N/A')} USD\n"
        markdown_content += f"  - Market Cap: ${bitcoin.get('usd_market_cap', 'N/A')} USD\n"
        markdown_content += f"  - 24h Volume: ${bitcoin.get('usd_24h_vol', 'N/A')} USD\n"
        markdown_content += f"  - 24h Change: {bitcoin.get('usd_24h_change', 'N/A')}%\n\n"

        markdown_content += f"- **Ethereum (ETH)**: ${ethereum.get('usd', 'N/A')} USD\n"
        markdown_content += f"  - Market Cap: ${ethereum.get('usd_market_cap', 'N/A')} USD\n"
        markdown_content += f"  - 24h Volume: ${ethereum.get('usd_24h_vol', 'N/A')} USD\n"
        markdown_content += f"  - 24h Change: {ethereum.get('usd_24h_change', 'N/A')}%\n\n"
    else:
        markdown_content += "No live cryptocurrency data available.\n\n"

    markdown_content += "## Trending Coins\n"
    if trending_data and trending_data.get("coins"):
        for coin in trending_data["coins"]:
            item = coin["item"]
            markdown_content += f"- **{item['name']} ({item['symbol'].upper()})**\n"
            markdown_content += f"  - Market Cap Rank: {item['market_cap_rank']}\n"
            markdown_content += f"  - Price (BTC): {item['price_btc']}\n"
            markdown_content += f"  - [More Info](https://www.coingecko.com/en/coins/{item['slug']})\n\n"
    else:
        markdown_content += "No trending coins available.\n\n"

    markdown_content += "## Posts\n"
    for post in posts:
        markdown_content += f"- **Post ID: {post['id']}**\n"
        markdown_content += f"  - Content:\n```\n{post['content']}\n```\n\n"

    return markdown_content

def save_markdown(content, file_path=MD_FILE):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        logging.info(f"Markdown data saved to {file_path}")
    except Exception as e:
        logging.error(f"Failed to save markdown file: {e}")

def main():
    input_file = POSTS_FILE

    # Print absolute path for debugging purposes
    abs_path = os.path.abspath(input_file)
    logging.info(f"Using file: {abs_path}")

    data = load_json(input_file)
    data = fix_duplicate_ids(data)
    save_json(data, input_file)

    # Fetch cryptocurrency data and trending coins
    crypto_data = fetch_crypto_data()
    trending_data = fetch_trending_data()
    posts = data.get("posts", [])  # Ensure posts are extracted from the data dictionary

    # Update post with cryptocurrency data
    for post in posts:
        if post["id"] == 1:
            post["content"] = "🚀 SOLANA GIVEAWAY 🚀\n\n🎁 Win 2.6 $SOL (~$1300)\n\n🤝 Follow @likhon_decrypto & @fariacrypto\n❤️ RT & Like\n💬 Comment your wallet\n\n⏳ 48 hrs! #SolanaGiveaway #Crypto"

    # Save updated posts
    save_json(data, input_file)

    # Create markdown content
    markdown_content = create_markdown(crypto_data, trending_data, posts)

    # Save markdown content to data.md
    save_markdown(markdown_content)

if __name__ == "__main__":
    main()
