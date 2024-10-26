# Fixing Duplicate IDs in JSON and Creating a Pull Request

This guide will help you fix duplicate IDs in a JSON file and create a pull request on the [Terminals-Pumps](https://github.com/likhonisaac/Terminals-Pumps) repository.

## Steps to Fix Duplicate IDs and Create a Pull Request

### Step 1: Clone the Repository

Open your terminal and clone the repository:

```sh
git clone https://github.com/likhonisaac/Terminals-Pumps.git
cd Terminals-Pumps
```

### Step 2: Create a New Branch

Create a new branch for your changes:

```sh
git checkout -b fix-duplicate-ids
```

### Step 3: Fix Duplicate IDs

Create a Python script to fix duplicate IDs in the JSON file. Save the following script as `fix_ids.py`:

```python
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
```

Run the script:

```sh
python fix_ids.py
```

### Step 4: Commit Your Changes

Add and commit your changes:

```sh
git add post/post.json
git commit -m "Fix duplicate IDs in post.json"
```

### Step 5: Push Your Changes

Push your changes to the remote repository:

```sh
git push origin fix-duplicate-ids
```

### Step 6: Create a Pull Request

1. Go to the repository on GitHub.
2. Click on the "Compare & pull request" button.
3. Provide a meaningful title and description for your pull request.
4. Click on "Create pull request".

