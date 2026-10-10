
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
    """Preserve old output keys for existing publishing integrations."""
    if not isinstance(data, dict):
        raise ValueError("AI response is not a JSON object")
    required = ("content", "facebook_content", "image_headline", "image_subheading",
                "facebook_image_headline", "facebook_image_subheading")
    if any(not isinstance(data.get(k), str) or not data[k].strip() for k in required):
        raise ValueError("Missing platform content or image copy")
    linked = data["content"].strip()
    face = data["facebook_content"].strip()
    if not 110 <= len(linked.split()) <= 260:
        raise ValueError("LinkedIn caption must be 110-260 words")
    if not 65 <= len(face.split()) <= 170:
        raise ValueError("Facebook caption must be 65-170 words")
    if linked.casefold() == face.casefold():
        raise ValueError("LinkedIn and Facebook captions must be different")
    for key in ("image_headline", "facebook_image_headline"):
        if len(data[key].strip()) > 58:
            raise ValueError(f"{key} too long")
    for key in ("image_subheading", "facebook_image_subheading"):
        if len(data[key].strip()) > 105:
            raise ValueError(f"{key} too long")
    if linked.count("#") > 3 or face.count("#") > 2:
        raise ValueError("Too many hashtags")
    banned = ("in today's digital landscape", "unlock your potential", "stop scrolling", "skyrocket your growth")
    if any(x in caption.lower() for caption in (linked, face) for x in banned):
        raise ValueError("Generic promotional wording detected")
    for key in ("linkedin_visual_points", "facebook_visual_points"):
        points = data.get(key)
        if not isinstance(points, list) or len(points) != 3 or any(not isinstance(p, str) or not 3 <= len(p.strip()) <= 38 for p in points):
            raise ValueError(f"{key}: expected 3 concise visual points (3-38 characters)")
    data["topic"] = topic
    data["content"] = linked  # IMPORTANT: existing LinkedIn publisher reads this
    data["facebook_content"] = face  # Facebook publisher should read this new key
    return data


def generate_post(topic, models, recent_topics):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    prompt = f"""You are a skilled B2B content strategist and editorial designer.
Create TWO ORIGINAL posts on the same focused idea in {topic}: one for LinkedIn and one for Facebook.
Today: {today}. Previously used ideas (avoid repeating angles): {json.dumps(recent_topics[-25:])}.

LINKEDIN (JSON key 'content'):
- 140-210 words; professional English, credible practical advice, natural confident tone.
- Start with a strong SPECIFIC insight or industry problem, not a cliche.
- Use useful short paragraphs and, when it aids scanning, a numbered list or 2-3 bullet points.
- At most 2 subtle markers such as →, •, or ✓; don't clutter with emoji.
- End with a relevant takeaway or thoughtful question; up to 3 precise hashtags.

FACEBOOK (JSON key 'facebook_content'):
- 80-125 words; distinct opening, distinct explanation and CTA, never a shortened LinkedIn copy.
- Friendly but professional, easy English, clear actionable tip or mini-checklist.
- Include 2-3 short list lines, each optionally beginning with ✓ or →.
- Keep it easy to scan. End with a natural helpful CTA, up to 2 hashtags.

VISUAL COPY:
- 'image_headline' (LinkedIn): sharp specific statement, 3-7 words, max 58 characters.
- 'image_subheading' (LinkedIn): one practical takeaway, max 105 characters.
- 'facebook_image_headline': different 3-7-word hook, max 58 characters.
- 'facebook_image_subheading': one concise takeaway, max 105 characters.
- Make headlines readable at a glance; NO hashtags, emoji, or fake statistics in image copy.
- 'linkedin_visual_points': exactly three distinct and specific short actionable labels (3-38 chars each).
- 'facebook_visual_points': exactly three different practical labels (3-38 chars each).
- Points MUST be relevant to the chosen topic/angle, not generic placeholders.

Never invent numerical results, client stories, experience, credentials, algorithm facts or guarantees.
Avoid hype, generic AI phrasing, emoji clutter, engagement bait, excessive hashtags and fake case studies.
Return ONLY valid JSON with string keys:
"title", "content", "facebook_content", "image_headline", "image_subheading", "facebook_image_headline", "facebook_image_subheading", "linkedin_visual_points", "facebook_visual_points".
The two visual_points keys must be arrays of exactly three strings; all other keys are strings.
"""
    errors = []
    for model in models:
        print(f"Trying model: {model}")
        url = f"{BASE_URL}/{model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 3200, "responseMimeType": "application/json"},
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
