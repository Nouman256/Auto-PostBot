
import os
import json
import re
import hashlib
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

BASE_URL = (
    "https://generativelanguage.googleapis.com/v1beta"
)

HEADERS = {
    "x-goog-api-key": API_KEY or "",
    "Content-Type": "application/json",
}

TOPICS = [
    "Web Development",
    "Search Engine Optimization (SEO)",
    "Digital Marketing",
]

MAX_RETRIES = 3
BASE_DELAY = 5
MAX_DELAY = 60

RETRYABLE_STATUS = {
    429, 500, 502, 503, 504
}

SESSION = requests.Session()


# ======================================
# SAFE ERROR HANDLING
# ======================================

def api_error_message(response):
    try:
        data = response.json()
        error = data.get("error", {})
        return str(
            error.get("message", "Unknown API error")
        )[:250]
    except (ValueError, AttributeError):
        return f"HTTP {response.status_code}"


def retry_delay(response, attempt):
    delay = min(
        BASE_DELAY * (2 ** attempt),
        MAX_DELAY
    )

    if response is not None:
        retry_after = response.headers.get(
            "Retry-After"
        )

        if retry_after:
            try:
                delay = max(
                    delay,
                    float(retry_after)
                )
            except ValueError:
                try:
                    retry_date = parsedate_to_datetime(
                        retry_after
                    )
                    remaining = (
                        retry_date -
                        datetime.now(timezone.utc)
                    ).total_seconds()

                    delay = max(
                        delay,
                        remaining
                    )
                except (ValueError, TypeError):
                    pass

    return min(
        max(0, delay) + random.uniform(0, 1),
        120
    )


# ======================================
# HTTP REQUEST WITH AUTO RETRY
# ======================================

def request_with_retry(
    method,
    url,
    *,
    timeout=60,
    **kwargs
):
    last_error = None

    for attempt in range(MAX_RETRIES):
        response = None

        try:
            response = SESSION.request(
                method,
                url,
                headers=HEADERS,
                timeout=timeout,
                **kwargs
            )

            if response.ok:
                return response

            status = response.status_code
            message = api_error_message(response)

            if status in (401, 403):
                raise RuntimeError(
                    f"Gemini authentication or "
                    f"permission error: HTTP {status}. "
                    f"{message}"
                )

            if status in (400, 404):
                raise ValueError(
                    f"Model incompatible or unavailable: "
                    f"HTTP {status}. {message}"
                )

            if status not in RETRYABLE_STATUS:
                raise RuntimeError(
                    f"Gemini API error HTTP {status}: "
                    f"{message}"
                )

            last_error = (
                f"HTTP {status}: {message}"
            )

            print(
                f"Temporary Gemini API error: "
                f"HTTP {status}"
            )

        except requests.RequestException as error:
            last_error = (
                f"Network error: {type(error).__name__}"
            )

            print(last_error)

        if attempt < MAX_RETRIES - 1:
            delay = retry_delay(
                response,
                attempt
            )

            print(
                f"Retrying in {delay:.1f} seconds "
                f"({attempt + 2}/{MAX_RETRIES})..."
            )

            time.sleep(delay)

    raise RuntimeError(
        f"Request failed after "
        f"{MAX_RETRIES} attempts. "
        f"Last error: {last_error}"
    )


# ======================================
# DISCOVER AVAILABLE MODELS
# ======================================

def get_available_models():
    print("Checking available Gemini models...")

    models = []
    page_token = None

    while True:
        params = {
            "pageSize": 100
        }

        if page_token:
            params["pageToken"] = page_token

        response = request_with_retry(
            "GET",
            f"{BASE_URL}/models",
            params=params,
            timeout=30
        )

        data = response.json()

        for model in data.get("models", []):
            name = model.get("name", "")

            methods = model.get(
                "supportedGenerationMethods", []
            )

            excluded_words = [
                "image",
                "audio",
                "tts",
                "embedding",
                "live",
            ]

            if (
                "generateContent" in methods
                and "gemini" in name.lower()
                and not any(
                    word in name.lower()
                    for word in excluded_words
                )
            ):
                models.append(name)

        page_token = data.get("nextPageToken")

        if not page_token:
            break

    def priority(name):
        lower = name.lower()

        if "flash-lite" in lower:
            return 0

        if "flash" in lower:
            return 1

        if "pro" in lower:
            return 3

        return 2

    models = sorted(
        set(models),
        key=lambda name: (
            priority(name),
            name
        )
    )

    print("Compatible Gemini models found:")

    for model in models:
        print("-", model)

    if not models:
        raise RuntimeError(
            "No compatible Gemini text models found."
        )

    return models


# ======================================
# EXTRACT AI RESPONSE
# ======================================

def extract_content(data):
    candidates = data.get(
        "candidates", []
    )

    if not candidates:
        raise ValueError(
            "No response candidates returned."
        )

    parts = candidates[0].get(
        "content", {}
    ).get("parts", [])

    content = "\n".join(
        part.get("text", "")
        for part in parts
        if isinstance(
            part.get("text"), str
        )
    ).strip()

    if not content:
        raise ValueError(
            "Gemini returned empty content."
        )

    return content


# ======================================
# GENERATE POST WITH MODEL FALLBACK
# ======================================

def validate_post(data, topic):
    if not isinstance(data, dict):
        raise ValueError("AI response is not a JSON object")
    required = ("content", "image_headline", "image_subheading")
    if any(not isinstance(data.get(k), str) or not data[k].strip() for k in required):
        raise ValueError("Missing content or image copy")
    content = data["content"].strip()
    words = len(content.split())
    if not 110 <= words <= 260:
        raise ValueError(f"Caption length outside 110-260 words: {words}")
    if len(data["image_headline"]) > 58 or len(data["image_subheading"]) > 105:
        raise ValueError("Image copy is too long")
    if content.count("#") > 3:
        raise ValueError("Too many hashtags")
    banned = ("in today's digital landscape", "unlock your potential", "stop scrolling", "skyrocket your growth")
    if any(x in content.lower() for x in banned):
        raise ValueError("Generic promotional wording detected")
    data["topic"] = topic
    data["content"] = content
    return data


def generate_post(topic, models, recent_topics):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    prompt = f"""You are an expert LinkedIn editorial strategist and technical practitioner.
Create ONE original, useful post for a digital marketing/web development professional.
Audience: founders, business owners, marketers, website owners, and potential B2B clients.
Today: {today}. Content pillar: {topic}.
Recently covered ideas (avoid similar angles): {json.dumps(recent_topics[-25:])}.

Think carefully before writing: select a narrow real-world problem, one defensible insight,
and a practical example or decision framework. Vary the opening and structure naturally.
Write natural professional ENGLISH only, 140-210 words, no filler or emojis.
Use short natural paragraphs, clear practical advice and at most 3 relevant hashtags.
No invented numbers, experiences, client stories, tests, news, platform changes or guarantees.
Never impersonate the author as having done work unless facts are supplied.
No engagement bait, generic motivational hooks, exaggerated claims, or artificial questions.
End naturally. Make the post specific enough to teach a reader something useful.
Image headline must be specific to this post, 3-8 words, <=58 characters.
Image subheading should summarize a concrete takeaway in <=105 characters.
Return ONLY valid JSON (no Markdown) with string keys:
"title", "content", "image_headline", "image_subheading".
"""
    errors = []
    for model in models:
        print(f"Trying model: {model}")
        url = f"{BASE_URL}/{model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1600, "responseMimeType": "application/json"},
        }
        try:
            response = request_with_retry("POST", url, json=payload, timeout=90)
            raw = extract_content(response.json()).strip()
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.I)
            post = validate_post(json.loads(raw), topic)
            return post, model
        except (ValueError, json.JSONDecodeError, RuntimeError) as error:
            if "authentication" in str(error).lower() or "permission error" in str(error).lower():
                raise
            errors.append(f"{model}: {error}")
            print("Model output rejected; trying next model")
    raise RuntimeError("Could not generate a quality-checked post: " + (errors[-1] if errors else "unknown"))


# ======================================
# MAIN
# ======================================

def main():
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY secret is missing")
    slot = os.getenv("POST_SLOT", "web").lower()
    slot_topics = {"web": TOPICS[0], "seo": TOPICS[1], "marketing": TOPICS[2]}
    if slot not in slot_topics:
        raise RuntimeError(f"Unknown POST_SLOT: {slot}")
    topic = slot_topics[slot]
    history_path = Path("post_history.json")
    history = json.loads(history_path.read_text(encoding="utf-8")) if history_path.exists() else []
    if not isinstance(history, list):
        history = []
    models = get_available_models()
    post, model = generate_post(topic, models, [x.get("title", "") for x in history if isinstance(x, dict)])
    post["model"] = model
    post["slot"] = slot
    post["created_at"] = datetime.now(timezone.utc).isoformat()
    Path("generated_posts.json").write_text(json.dumps([post], ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Created one validated {topic} post: {len(post['content'])} characters")


if __name__ == "__main__":
    main()
