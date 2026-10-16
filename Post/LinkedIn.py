import os
import json
from pathlib import Path
import requests

def get_access_token():
    return os.getenv("LINKEDIN_ACCESS_TOKEN")

def get_person_urn(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    response = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers)
    if response.status_code == 200:
        data = response.json()
        sub = data.get("sub")
        if sub:
            print("LinkedIn personal profile verified")
            return f"urn:li:person:{sub}"
    
    # Fallback to standard me endpoint
    res = requests.get("https://api.linkedin.com/v2/me", headers=headers)
    if res.status_code == 200:
        print("LinkedIn profile verified via /me")
        return f"urn:li:person:{res.json().get('id')}"
    
    raise RuntimeError(f"Failed to get LinkedIn URN: {response.text} | {res.text}")

def register_upload(access_token, author_urn):
    url = "https://api.linkedin.com/v2/assets?action=registerUpload"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    body = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": author_urn,
            "serviceRelationships": [{
                "relationshipType": "OWNER",
                "identifier": "urn:li:userGeneratedContent"
            }]
        }
    }
    response = requests.post(url, headers=headers, json=body)
    if not response.ok:
        raise RuntimeError(f"Failed to register image upload: {response.text}")
    data = response.json().get("value", {})
    upload_url = data.get("uploadMechanism", {}).get("com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest", {}).get("uploadUrl")
    asset = data.get("asset")
    return upload_url, asset

def upload_image(upload_url, image_path, access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    with open(image_path, "rb") as f:
        image_data = f.read()
    response = requests.put(upload_url, headers=headers, data=image_data)
    if not response.ok:
        raise RuntimeError(f"Failed to upload image binary: {response.text}")
    print("Image uploaded successfully")

def post_to_linkedin(text, image_path, access_token, author_urn):
    upload_url, asset = register_upload(access_token, author_urn)
    upload_image(upload_url, image_path, access_token)
    
    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    body = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "IMAGE",
                "media": [{
                    "status": "READY",
                    "description": {"text": "Automated tech insights"},
                    "media": asset,
                    "title": {"text": "Tech Insights"}
                }]
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    response = requests.post(url, headers=headers, json=body)
    if not response.ok:
        raise RuntimeError(f"Failed to create LinkedIn post: {response.text}")
    
    post_id = response.json().get("id")
    print(f"LinkedIn post published successfully!")
    print(f"Post ID: {post_id}")
    return post_id

def main():
    token = get_access_token()
    if not token:
        raise RuntimeError("LINKEDIN_ACCESS_TOKEN is missing")
    
    posts_path = Path("generated_posts.json")
    if not posts_path.exists():
        print("No generated_posts.json found.")
        return
    
    posts = json.loads(posts_path.read_text(encoding="utf-8"))
    if not posts:
        return
    
    post = posts[0]
    text = post.get("content", "")
    image_path = post.get("image_path", "")
    
    print(f"Caption characters: {len(text)}")
    print(f"Image: {image_path}")
    
    author_urn = get_person_urn(token)
    post_id = post_to_linkedin(text, image_path, token, author_urn)
    
    # Safe history update to avoid KeyError
    history_path = Path("post_history.json")
    history = json.loads(history_path.read_text(encoding="utf-8")) if history_path.exists() else []
    if not isinstance(history, list):
        history = []
        
    history.append({
        "title": post.get("title", "LinkedIn Post"),
        "topic": post.get("topic", "General"),
        "slot": post.get("slot", "technical"),
        "platform": "linkedin",
        "post_id": post_id,
        "created_at": post.get("created_at")
    })
    history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
