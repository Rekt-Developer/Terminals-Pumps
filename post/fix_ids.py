import json
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_json(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load JSON file: {e}")
        sys.exit(1)

def save_json(data, file_path):
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        logging.info(f"JSON data saved to {file_path}")
    except Exception as e:
        logging.error(f"Failed to save JSON file: {e}")
        sys.exit(1)

def fix_duplicate_ids(data):
    unique_id = 1
    seen_ids = set()
    for post in data["posts"]:
        if post["id"] in seen_ids:
            post["id"] = unique_id
            unique_id += 1
        seen_ids.add(post["id"])
    logging.info("Duplicate IDs fixed")
    return data

def main():
    input_file = 'post/post.json'
    data = load_json(input_file)
    data = fix_duplicate_ids(data)
    save_json(data, input_file)

if __name__ == "__main__":
    main()
