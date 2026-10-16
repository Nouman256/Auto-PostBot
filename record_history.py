import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

POST_FILE = Path("generated_posts.json")
HISTORY_FILE = Path("post_history.json")

def main():
    posts = json.loads(POST_FILE.read_text(encoding="utf-8"))
    history = []
    if HISTORY_FILE.exists():
        try:
            existing = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            if isinstance(existing, list):
                history = existing
        except json.JSONDecodeError:
            print("Warning: history file invalid; starting a fresh history list")
    seen = {item.get("dedupe_key") for item in history if isinstance(item, dict)}
    now = datetime.now(timezone.utc).isoformat()
    for post in posts:
        key = post.get("dedupe_key") or hashlib.sha256(
            f"{post.get('run_date')}|{post.get('category')}|{post.get('title')}".encode()
        ).hexdigest()[:20]
        if key in seen:
            print(f"History already contains this concept key: {key}")
            continue
        history.append({
            "title": post.get("title", ""),
            "topic": post.get("topic", ""),
            "category": post.get("category", ""),
            "run_date": post.get("run_date", ""),
            "dedupe_key": key,
            "linkedin_post_id": post.get("_linkedin_post_id", ""),
            "facebook_post_id": post.get("_facebook_post_id", ""),
            "published_at": now,
            "mode": "published" if post.get("_linkedin_post_id") or post.get("_facebook_post_id") else "dry_run",
        })
        seen.add(key)
    HISTORY_FILE.write_text(json.dumps(history[-500:], ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"History updated: {len(history[-500:])} records retained")

if __name__ == "__main__":
    main()
