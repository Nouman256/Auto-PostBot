import os
import json
import re
from pathlib import Path
import time
import random
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests

# ======================================
# CONFIGURATION
# ======================================

API_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

HEADERS = {
    "x-goog-api-key": API_KEY or "",
    "Content-Type": "application/json",
}

# Naye Slots aur Categories
CATEGORIES = {
    "technical": [
        "WordPress Speed Optimization & Core Web Vitals",
        "On-Page SEO Best Practices & Keyword Strategy",
        "Kadence & Elementor WordPress Development Tips"
    ],
    "entertainment": [
        "Web Developer vs Client Funny Realities & Memes",
        "Coding Struggles, Bugs & Coffee Humor",
        "Web Development & SEO Engaging Community Polls / Questions"
    ]
}

MAX_RETRIES = 3
BASE_DELAY = 5
MAX_DELAY = 60
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
SESSION = requests.Session()


def api_error_message(response):
    try:
        data = response.json()
        error = data.get("error", {})
        return str(error.get("message", "Unknown API error"))[:250]
    except (ValueError, AttributeError):
        return f"HTTP {response.status_code}"


def retry_delay(response, attempt):
    delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
    return min(max(0, delay) + random.uniform(0, 1), 120)


def request_with_retry(method, url, *, timeout=60, **kwargs):
    last_error = None
    for attempt in range(MAX_RETRIES):
        response = None
        try:
            response = SESSION.request(method, url, headers=HEADERS, timeout=timeout, **kwargs)
            if response.ok:
                return response
            status = response.status_code
            message = api_error_message(response)
            if status in (401, 403):
                raise RuntimeError(f"Gemini auth error: HTTP {status}. {message}")
            if status in (400, 404):
                raise ValueError(f"Model unavailable: HTTP {status}. {message}")
            if status not in RETRYABLE_STATUS:
                raise RuntimeError(f"Gemini API error HTTP {status}: {message}")
            last_error = f"HTTP {status}: {message}"
        except requests.RequestException as error:
            last_error = f"Network error: {type(error).__name__}"
        if attempt < MAX_RETRIES - 1:
            time.sleep(retry_delay(response, attempt))
    raise RuntimeError(f"Request failed after {MAX_RETRIES} attempts. Last error: {last_error}")


def get_available_models():
    models = []
    page_token = None
    while True:
        params = {"pageSize": 100}
        if page_token:
            params["pageToken"] = page_token
        response = request_with_retry("GET", f"{BASE_URL}/models", params=params, timeout=30)
        data = response.json()
        for model in data.get("models", []):
            name = model.get("name", "")
            methods = model.get("supportedGenerationMethods", [])
            if "generateContent" in methods and "gemini" in name.lower() and not any(w in name.lower() for w in ["image", "audio", "tts", "embedding", "live"]):
                models.append(name)
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return sorted(set(models), key=lambda n: (0 if "flash-lite" in n.lower() else 1 if "flash" in n.lower() else 3 if "pro" in n.lower() else 2, n))


def extract_content(data):
    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError("No response candidates returned.")
    parts = candidates[0].get("content", {}).get("parts", [])
    content = "\n".join(part.get("text", "") for part in parts if isinstance(part.get("text"), str)).strip()
    if not content:
        raise ValueError("Gemini returned empty content.")
    return content


def validate_post(data, topic, slot):
    if not isinstance(data, dict):
        raise ValueError("AI response is not a JSON object")
    required = ("content", "facebook_content", "image_headline", "image_subheading",
                "facebook_image_headline", "facebook_image_subheading")
    if any(not isinstance(data.get(k), str) or not data[k].strip() for k in required):
        raise ValueError("Missing platform content or image copy")
    linked = data["content"].strip()
    face = data["facebook_content"].strip()
    
    data["topic"] = topic
    data["slot"] = slot
    return data


def generate_post(slot, models, recent_topics):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    topics_list = CATEGORIES.get(slot, CATEGORIES["technical"])
    topic = random.choice(topics_list)

    if slot == "technical":
        focus_instruction = "Create a HIGHLY PRACTICAL technical post about Web Development, WordPress, or SEO with actionable steps."
    else:
        focus_instruction = "Create an ENTERTAINING, relatable developer meme concept, office humor, or an engaging community question/poll."

    prompt = f"""You are a skilled B2B content strategist and social media creator.
{focus_instruction}
Topic/Angle: {topic}
Today: {today}. Avoid repeating these recent angles: {json.dumps(recent_topics[-25:])}.

LINKEDIN (JSON key 'content'):
- Professional English, credible, engaging tone. 110-210 words. Up to 3 hashtags.

FACEBOOK (JSON key 'facebook_content'):
- Casual, friendly, highly engaging tone (different from LinkedIn). 70-150 words. Up to 2 hashtags.

VISUAL COPY & AI IMAGE PROMPT:
- 'image_headline' (LinkedIn): sharp hook, max 58 chars.
- 'image_subheading' (LinkedIn): practical takeaway, max 105 chars.
- 'facebook_image_headline': different casual hook, max 58 chars.
- 'facebook_image_subheading': concise takeaway, max 105 chars.
- 'linkedin_visual_points' & 'facebook_visual_points': exactly three short labels (3-38 chars each).
- 'ai_image_prompt': A detailed visual description for an AI image generator representing this post (e.g. professional tech setup or funny developer meme style, high quality).

Return ONLY valid JSON with string/array keys:
"title", "content", "facebook_content", "image_headline", "image_subheading", "facebook_image_headline", "facebook_image_subheading", "linkedin_visual_points", "facebook_visual_points", "ai_image_prompt".
"""
    errors = []
    for model in models:
        url = f"{BASE_URL}/{model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 3200, "responseMimeType": "application/json"},
        }
        try:
            response = request_with_retry("POST", url, json=payload, timeout=90)
            raw = extract_content(response.json()).strip()
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=I if 'I' in globals() else re.IGNORECASE)
            post = validate_post(json.loads(raw), topic, slot)
            post["model"] = model
            return post
        except (ValueError, json.JSONDecodeError, RuntimeError) as error:
            errors.append(f"{model}: {error}")
    raise RuntimeError("Could not generate post: " + (errors[-1] if errors else "unknown"))


def main():
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY secret is missing")
    slot = os.getenv("POST_SLOT", "technical").lower()
    if slot not in CATEGORIES:
        slot = "technical"

    history_path = Path("post_history.json")
    history = json.loads(history_path.read_text(encoding="utf-8")) if history_path.exists() else []
    if not isinstance(history, list):
        history = []

    models = get_available_models()
    post = generate_post(slot, models, [x.get("title", "") for x in history if isinstance(x, dict)])
    post["created_at"] = datetime.now(timezone.utc).isoformat()
    
    Path("generated_posts.json").write_text(json.dumps([post], ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Created validated {slot} post successfully.")


if __name__ == "__main__":
    main()
