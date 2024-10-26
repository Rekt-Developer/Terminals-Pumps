import json

# Load the JSON data
with open('post/post.json', 'r') as f:
    data = json.load(f)

# Fix duplicate IDs
unique_id = 1
seen_ids = set()
for post in data["posts"]:
    if post["id"] in seen_ids:
        post["id"] = unique_id
        unique_id += 1
    seen_ids.add(post["id"])

# Save the fixed JSON data
with open('post/post.json', 'w') as f:
    json.dump(data, f, indent=4)

print("Duplicate IDs fixed and saved to post/post.json")
