import json
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_json(file_path):
    try:
        # Check if the file exists
        if not os.path.exists(file_path):
            logging.error(f"File does not exist: {file_path}")
            sys.exit(1)

        # Explicitly open with UTF-8 encoding to preserve emojis and special characters
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
        # Explicitly save with UTF-8 encoding to preserve emojis and special characters
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)  # ensure_ascii=False preserves emojis
        logging.info(f"JSON data saved to {file_path}")
    except Exception as e:
        logging.error(f"Failed to save JSON file: {e}")
        sys.exit(1)

def fix_duplicate_ids(data):
    unique_id = 1
    seen_ids = set()
    for post in data.get("posts", []):
        # Only modify the 'id' field and leave everything else unchanged
        if post["id"] in seen_ids:
            logging.info(f"Duplicate ID {post['id']} found. Assigning new ID: {unique_id}")
            post["id"] = unique_id
            unique_id += 1
        seen_ids.add(post["id"])
    logging.info("Duplicate IDs fixed")
    return data

def main():
    input_file = 'post/post.json'
    
    # Print absolute path for debugging purposes
    abs_path = os.path.abspath(input_file)
    logging.info(f"Using file: {abs_path}")
    
    data = load_json(input_file)
    data = fix_duplicate_ids(data)
    save_json(data, input_file)

if __name__ == "__main__":
    main()
