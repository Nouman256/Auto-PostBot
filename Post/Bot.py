
import os
import json
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

def generate_post(topic, models):
    today = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")

    prompt = f"""
You are a professional social media content writer.

Date: {today}
Topic category: {topic}

Create one original educational social media post.

Requirements:
- Write in English and Urdu script.
- Give practical and accurate advice.
- Use a professional, engaging tone.
- Maximum 250 words total.
- Include a strong opening.
- Add a practical example or useful tip.
- Add 3 to 5 relevant hashtags.
- Avoid fake statistics and unsupported claims.
- Do not invent recent news.
- Make the post suitable for LinkedIn,
  Facebook and Telegram.
- Return only the final post.
"""

    errors = []

    for model in models:
        print(f"Trying model: {model}")

        url = (
            f"{BASE_URL}/{model}:generateContent"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.8,
                "maxOutputTokens": 1200
            }
        }

        try:
            response = request_with_retry(
                "POST",
                url,
                json=payload,
                timeout=90
            )

            content = extract_content(
                response.json()
            )

            print(
                f"Post generated with {model}"
            )

            return content, model

        except ValueError as error:
            errors.append(
                f"{model}: {error}"
            )

            print(
                "Model incompatible or empty. "
                "Trying next model..."
            )

        except RuntimeError as error:
            error_text = str(error)

            if (
                "authentication" in error_text.lower()
                or "permission error" in error_text.lower()
            ):
                raise

            errors.append(
                f"{model}: {error_text}"
            )

            print(
                "Model failed. "
                "Trying next model..."
            )

    raise RuntimeError(
        "All compatible Gemini models failed. "
        "Last error: "
        + (
            errors[-1]
            if errors
            else "Unknown error"
        )
    )


# ======================================
# MAIN
# ======================================

def main():
    if not API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY secret is missing."
        )

    print("AI Auto Post Bot Started")

    models = get_available_models()

    posts = []

    for topic in TOPICS:
        print(
            f"\nGenerating post: {topic}"
        )

        content, model = generate_post(
            topic,
            models
        )

        posts.append({
            "topic": topic,
            "model": model,
            "content": content,
            "created_at": datetime.now(
                timezone.utc
            ).isoformat()
        })

        print(
            f"Generated {len(content)} "
            f"characters for {topic}"
        )

        print("-" * 50)

        time.sleep(2)

    with open(
        "generated_posts.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            posts,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"Successfully generated "
        f"{len(posts)} posts!"
    )


if __name__ == "__main__":
    main()
