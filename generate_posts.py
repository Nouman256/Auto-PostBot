import os
import json
import re
import random
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests

API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
HEADERS = {"x-goog-api-key": API_KEY, "Content-Type": "application/json"}
MAX_RETRIES = 3
BASE_DELAY = 5
MAX_DELAY = 60
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
SESSION = requests.Session()
POST_FILE = Path("generated_posts.json")
HISTORY_FILE = Path("post_history.json")

def api_error_message(response):
    try:
        return str(response.json().get("error", {}).get("message", "Unknown API error"))[:250]
    except (ValueError, AttributeError):
        return f"HTTP {response.status_code}"

def retry_delay(response, attempt):
    delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                delay = max(delay, float(retry_after))
            except ValueError:
                try:
                    delay = max(delay, (parsedate_to_datetime(retry_after) - datetime.now(timezone.utc)).total_seconds())
                except (ValueError, TypeError):
                    pass
    return min(max(0, delay) + random.uniform(0, 1), 120)

def request_with_retry(method, url, *, timeout=60, **kwargs):
    last_error = "unknown"
    for attempt in range(MAX_RETRIES):
        response = None
        try:
            response = SESSION.request(method, url, headers=HEADERS, timeout=timeout, **kwargs)
            if response.ok:
                return response
            status = response.status_code
            message = api_error_message(response)
            if status in (401, 403):
                raise RuntimeError(f"Gemini authentication/permission error HTTP {status}: {message}")
            if status in (400, 404):
                raise ValueError(f"Gemini model/API incompatible HTTP {status}: {message}")
            if status not in RETRYABLE_STATUS:
                raise RuntimeError(f"Gemini API error HTTP {status}: {message}")
            last_error = f"HTTP {status}: {message}"
        except requests.RequestException as exc:
            last_error = f"Network error: {type(exc).__name__}"
        if attempt < MAX_RETRIES - 1:
            delay = retry_delay(response, attempt)
            print(f"Temporary Gemini error; retrying in {delay:.1f}s")
            import time
            time.sleep(delay)
    raise RuntimeError(f"Gemini request failed after {MAX_RETRIES} attempts: {last_error}")

def get_available_models():
    models, page_token = [], None
    while True:
        params = {"pageSize": 100}
        if page_token:
            params["pageToken"] = page_token
        response = request_with_retry("GET", f"{BASE_URL}/models", params=params, timeout=30)
        data = response.json()
        for model in data.get("models", []):
            name = model.get("name", "")
            methods = model.get("supportedGenerationMethods", [])
            excluded = ("image", "audio", "tts", "embedding", "live")
            if "generateContent" in methods and "gemini" in name.lower() and not any(x in name.lower() for x in excluded):
                models.append(name)
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    def priority(name):
        lower = name.lower()
        if "flash-lite" in lower: return 0
        if "flash" in lower: return 1
        if "pro" in lower: return 3
        return 2
    models = sorted(set(models), key=lambda x: (priority(x), x))
    if not models:
        raise RuntimeError("No compatible Gemini text models found.")
    print("Gemini models:", ", ".join(models))
    return models

def extract_content(data):
    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError("Gemini returned no candidates.")
    parts = candidates[0].get("content", {}).get("parts", [])
    content = "\n".join(p.get("text", "") for p in parts if isinstance(p.get("text"), str)).strip()
    if not content:
        raise ValueError("Gemini returned empty content.")
    return content

def load_history():
    if not HISTORY_FILE.exists():
        return []
    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []

def validate_post(post, expected_category):
    if not isinstance(post, dict):
        raise ValueError("AI response is not an object")
    required = [
        "title", "topic", "category", "content", "facebook_content",
        "image_headline", "image_subheading",
        "facebook_image_headline", "facebook_image_subheading",
    ]
    for key in required:
        if not isinstance(post.get(key), str) or not post[key].strip():
            raise ValueError(f"Missing field: {key}")
    post["category"] = expected_category
    post["topic"] = post["topic"].strip()
    linked = post["content"].strip()
    face = post["facebook_content"].strip()
    if linked.casefold() == face.casefold():
        raise ValueError("Platform captions must differ")
    if expected_category == "technical":
        if not 110 <= len(linked.split()) <= 230:
            raise ValueError("Technical LinkedIn caption must be 110-230 words")
        if not 65 <= len(face.split()) <= 150:
            raise ValueError("Technical Facebook caption must be 65-150 words")
    else:
        if not 35 <= len(linked.split()) <= 140:
            raise ValueError("Engagement LinkedIn caption must be 35-140 words")
        if not 20 <= len(face.split()) <= 100:
            raise ValueError("Engagement Facebook caption must be 20-100 words")
    for key in ("image_headline", "facebook_image_headline"):
        if len(post[key]) > 58:
            raise ValueError(f"{key} must be <= 58 characters")
    for key in ("image_subheading", "facebook_image_subheading"):
        if len(post[key]) > 105:
            raise ValueError(f"{key} must be <= 105 characters")
    if linked.count("#") > 3 or face.count("#") > 2:
        raise ValueError("Too many hashtags")
    banned = ("in today's digital landscape", "unlock your potential", "stop scrolling", "skyrocket your growth")
    if any(term in cap.lower() for cap in (linked, face) for term in banned):
        raise ValueError("Generic promotional wording detected")
    post["content"] = linked
    post["facebook_content"] = face
    return post

def generate_category(category, models, recent_titles):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if category == "technical":
        category_brief = """
Create ONE genuinely useful technical/educational post about web development, WordPress,
website performance, accessibility, website security, technical SEO, on-page SEO, or e-commerce.
Choose one narrow, practical idea. No unsupported stats, fabricated case studies, guarantees,
or claims about secret ranking factors. Provide steps or a useful diagnostic.
LinkedIn: 110-200 words, professional and insightful, at most 3 relevant hashtags.
Facebook: 65-130 words, friendlier and more scannable; NOT a shortened LinkedIn version.
"""
    else:
        category_brief = """
Create ONE engaging, brand-safe social post for a digital agency audience. Choose either:
a relatable web/SEO/client-work meme, a thoughtful poll/question, or a light professional joke.
Do not demean clients or professions, use offensive humor, or use copyrighted character imagery.
It must still relate to websites, SEO, online business, design, or digital work.
LinkedIn: 40-100 words, conversation-starting but not engagement bait.
Facebook: 25-80 words, casual and distinct from LinkedIn.
If it's a meme, write an original relatable setup; if a question/poll, give clear choices.
"""
    prompt = f"""You are the editorial and visual-content strategist for TechVision Digital,
a web development, WordPress, SEO and digital services business.
Date: {today}
Category: {category}
Previously used titles/ideas to avoid: {json.dumps(recent_titles[-60:], ensure_ascii=False)}

{category_brief}

Generate different platform-specific captions and image text. The visual should match the exact idea.
Image headline: 3-7 words, <=58 characters. Subheading: one concise practical line <=105 characters.
Facebook headline/subheading must be different from LinkedIn's.
Return ONLY valid JSON with these string keys:
"title", "topic", "category", "content", "facebook_content",
"image_headline", "image_subheading",
"facebook_image_headline", "facebook_image_subheading".
Set category exactly to "{category}". No markdown fences.
"""
    errors = []
    for model in models:
        print(f"Generating {category} post with {model}")
        url = f"{BASE_URL}/{model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.8 if category == "engagement" else 0.65,
                "maxOutputTokens": 2600,
                "responseMimeType": "application/json",
            },
        }
        try:
            response = request_with_retry("POST", url, json=payload, timeout=90)
            raw = extract_content(response.json()).strip()
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.I)
            post = validate_post(json.loads(raw), category)
            post["model"] = model
            return post
        except (ValueError, json.JSONDecodeError, RuntimeError) as exc:
            if "authentication" in str(exc).lower() or "permission" in str(exc).lower():
                raise
            errors.append(f"{model}: {exc}")
            print(f"Rejected output from {model}: {exc}")
    raise RuntimeError(f"Unable to generate valid {category} post: {errors[-1] if errors else 'unknown'}")

def main():
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY secret is missing")
    history = load_history()
    recent_titles = [str(item.get("title", "")) for item in history if isinstance(item, dict)]
    models = get_available_models()
    posts = [
        generate_category("technical", models, recent_titles),
        generate_category("engagement", models, recent_titles),
    ]
    # Stable daily key protects against accidental reruns of the same scheduled date.
    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for post in posts:
        post["run_date"] = run_date
        post["created_at"] = datetime.now(timezone.utc).isoformat()
        post["dedupe_key"] = hashlib.sha256(
            f"{run_date}|{post['category']}|{post['title'].casefold()}".encode("utf-8")
        ).hexdigest()[:20]
    POST_FILE.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Generated and validated 2 unique post concepts:")
    for post in posts:
        print(f"- {post['category']}: {post['title']}")

if __name__ == "__main__":
    main()
