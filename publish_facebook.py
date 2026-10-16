import os
import json
from pathlib import Path
import requests

PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "").strip()
PAGE_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip()
API_VERSION = os.getenv("FACEBOOK_API_VERSION", "v26.0")
PUBLISH = os.getenv("PUBLISH_FACEBOOK", "false").lower() == "true"
POST_FILE = Path("generated_posts.json")

def publish_one(post):
    if not PAGE_ID:
        raise RuntimeError("FACEBOOK_PAGE_ID is missing")
    if not PAGE_TOKEN:
        raise RuntimeError("FACEBOOK_PAGE_ACCESS_TOKEN is missing")
    caption = post["facebook_content"].strip()
    image_path = Path(post["facebook_image_path"])
    if not image_path.is_file():
        raise FileNotFoundError(f"Facebook image missing: {image_path}")
    url = f"https://graph.facebook.com/{API_VERSION}/{PAGE_ID}/photos"
    with image_path.open("rb") as image:
        response = requests.post(
            url,
            data={"caption": caption, "published": "true"},
            files={"source": (image_path.name, image, "image/png")},
            headers={"Authorization": f"Bearer {PAGE_TOKEN}"},
            timeout=90,
        )
    try:
        result = response.json()
    except ValueError:
        raise RuntimeError("Facebook API returned invalid JSON")
    if not response.ok or "id" not in result:
        error = result.get("error", {})
        raise RuntimeError(f"Facebook publishing failed: {error.get('message', response.status_code)}")
    return result.get("post_id") or result["id"]

def main():
    posts = json.loads(POST_FILE.read_text(encoding="utf-8"))
    if not isinstance(posts, list) or len(posts) != 2:
        raise RuntimeError("Expected two generated posts")
    for post in posts:
        print(f"Facebook [{post['category']}]: {post['title']}")
        print(f"Image: {post.get('facebook_image_path')}")
    if not PUBLISH:
        print("FACEBOOK DRY RUN: no posts published")
        return
    for post in posts:
        post_id = publish_one(post)
        post["_facebook_post_id"] = post_id
        print(f"Facebook published [{post['category']}], ID: {post_id}")
    POST_FILE.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
