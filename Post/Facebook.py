import os
import json
from pathlib import Path
import requests

def post_to_facebook():
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    access_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    
    if not page_id or not access_token:
        raise RuntimeError("Facebook Page ID or Access Token is missing")
        
    posts_path = Path("generated_posts.json")
    if not posts_path.exists():
        print("No generated_posts.json found.")
        return
        
    posts = json.loads(posts_path.read_text(encoding="utf-8"))
    if not posts:
        return
        
    post = posts[0]
    text = post.get("facebook_content") or post.get("content", "")
    image_path = post.get("facebook_image_path") or post.get("image_path", "")
    
    url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
    
    with open(image_path, "rb") as img_file:
        files = {
            "source": img_file
        }
        data = {
            "caption": text,
            "access_token": access_token
        }
        
        response = requests.post(url, data=data, files=files)
        if not response.ok:
            raise RuntimeError(f"Failed to post to Facebook: {response.text}")
            
        res_data = response.json()
        post_id = res_data.get("post_id") or res_data.get("id")
        print(f"Facebook post published successfully! ID: {post_id}")
        
        # Safe history update
        history_path = Path("post_history.json")
        history = json.loads(history_path.read_text(encoding="utf-8")) if history_path.exists() else []
        if not isinstance(history, list):
            history = []
            
        history.append({
            "title": post.get("title", "Facebook Post"),
            "topic": post.get("topic", "General"),
            "slot": post.get("slot", "technical"),
            "platform": "facebook",
            "post_id": post_id,
            "created_at": post.get("created_at")
        })
        history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    post_to_facebook()
