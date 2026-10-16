import os
import json
import hashlib
from pathlib import Path
import requests

TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip()
VERSION = os.getenv("LINKEDIN_VERSION", "202609")
PUBLISH = os.getenv("PUBLISH_LINKEDIN", "false").lower() == "true"
API = "https://api.linkedin.com"
POST_FILE = Path("generated_posts.json")
HISTORY_FILE = Path("post_history.json")
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Linkedin-Version": VERSION,
    "X-Restli-Protocol-Version": "2.0.0",
    "Accept": "application/json",
}

def check(response, action):
    if not response.ok:
        try:
            message = response.json().get("message", "API error")
        except ValueError:
            message = response.text[:250]
        raise RuntimeError(f"{action} failed: HTTP {response.status_code} - {message}")

def author_urn():
    response = requests.get(
        f"{API}/v2/userinfo",
        headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"},
        timeout=30,
    )
    check(response, "LinkedIn authentication")
    sub = response.json().get("sub")
    if not sub:
        raise RuntimeError("LinkedIn member ID missing")
    print("LinkedIn personal profile verified")
    return f"urn:li:person:{sub}"

def upload_image(author, path):
    response = requests.post(
        f"{API}/rest/images?action=initializeUpload",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"initializeUploadRequest": {"owner": author}},
        timeout=30,
    )
    check(response, "Image initialization")
    value = response.json()["value"]
    with open(path, "rb") as file:
        uploaded = requests.put(
            value["uploadUrl"],
            headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "image/png"},
            data=file,
            timeout=120,
        )
    check(uploaded, "Image upload")
    return value["image"]

def publish_one(author, post):
    caption = post["content"].strip()
    path = Path(post["image_path"])
    if not path.is_file():
        raise FileNotFoundError(f"LinkedIn image missing: {path}")
    image_urn = upload_image(author, path)
    payload = {
        "author": author,
        "commentary": caption,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "content": {"media": {"id": image_urn, "altText": post.get("image_subheading", "TechVision Digital post graphic")}},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    response = requests.post(
        f"{API}/rest/posts",
        headers={**HEADERS, "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    check(response, "LinkedIn publishing")
    if response.status_code != 201:
        raise RuntimeError(f"Unexpected LinkedIn publishing response: {response.status_code}")
    return response.headers.get("x-restli-id", "")

def main():
    if not TOKEN:
        raise RuntimeError("LINKEDIN_ACCESS_TOKEN missing")
    posts = json.loads(POST_FILE.read_text(encoding="utf-8"))
    if not isinstance(posts, list) or len(posts) != 2:
        raise RuntimeError("Expected two generated posts")
    # Authentication check is read-only and safe in dry-run mode.
    author = author_urn()
    for post in posts:
        print(f"LinkedIn [{post['category']}]: {post['title']}")
        print(f"Image: {post.get('image_path')}")
    if not PUBLISH:
        print("LINKEDIN DRY RUN: no posts published")
        return
    for post in posts:
        post_id = publish_one(author, post)
        post["_linkedin_post_id"] = post_id
        print(f"LinkedIn published [{post['category']}], ID: {post_id}")
    POST_FILE.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
