
import os
import json
import time
from datetime import datetime, timezone

import requests

API_KEY = os.getenv("GEMINI_API_KEY")

BASE_URL = (
    "https://generativelanguage.googleapis.com/v1beta"
)

HEADERS = {
    "x-goog-api-key": API_KEY or "",
    "Content-Type": "application/json"
}

TOPICS = [
    "Web Development",
    "Search Engine Optimization (SEO)",
    "Digital Marketing"
]


def get_available_models():
    print("Checking available Gemini models...")

    models = []
    page_token = None

    while True:
        params = {"pageSize": 100}

        if page_token:
            params["pageToken"] = page_token

        response = requests.get(
            f"{BASE_URL}/models",
            headers=HEADERS,
            params=params,
            timeout=30
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Model discovery failed: "
                f"HTTP {response.status_code} "
                f"{response.text[:300]}"
            )

        data = response.json()

        for model in data.get("models", []):
            name = model.get("name", "")
            methods = model.get(
                "supportedGenerationMethods", []
            )

            if (
                "generateContent" in methods
                and "gemini" in name.lower()
                and not any(
                    word in name.lower()
                    for word in [
                        "image",
                        "audio",
                        "tts",
                        "embedding",
                        "live"
                    ]
                )
            ):
                models.append(name)

        page_token = data.get("nextPageToken")

        if not page_token:
            break

    # Prefer lightweight text models.
    def priority(name):
        lower = name.lower()

        if "flash-lite" in lower:
            return 0
        if "flash" in lower:
            return 1
        if "pro" in lower:
            return 3
        return 2

    models = sorted(set(models), key=priority)

    print("Available text models:")
    for model in models:
        print("-", model)

    if not models:
        raise RuntimeError(
            "No compatible Gemini text models found."
        )

    return models


def generate_post(topic, models):
    today = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d"
    )

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
- Make the post suitable for Facebook
  and Telegram.
- Return only the final post.
"""

    last_error = None

    for model in models:
        print(f"Trying model: {model}")

        url = (
            f"{BASE_URL}/{model}:generateContent"
        )

        for attempt in range(2):
            try:
                response = requests.post(
                    url,
                    headers=HEADERS,
                    json={
                        "contents": [
                            {
                                "parts": [
                                    {"text": prompt}
                                ]
                            }
                        ],
                        "generationConfig": {
                            "temperature": 0.8,
                            "maxOutputTokens": 1200
                        }
                    },
                    timeout=90
                )

                if response.status_code == 200:
                    data = response.json()

                    candidates = data.get(
                        "candidates", []
                    )

                    if not candidates:
                        raise RuntimeError(
                            "No candidates returned."
                        )

                    parts = candidates[0].get(
                        "content", {}
                    ).get("parts", [])

                    content = "\n".join(
                        part.get("text", "")
                        for part in parts
                    ).strip()

                    if not content:
                        raise RuntimeError(
                            "Empty AI response."
                        )

                    return content, model

                if response.status_code in (
                    400, 404
                ):
                    print(
                        f"Model unavailable or "
                        f"incompatible: {model}"
                    )
                    break

                if response.status_code == 429:
                    raise RuntimeError(
                        "API quota or rate limit reached. "
                        "Check your free-tier limits."
                    )

                if response.status_code in (
                    401, 403
                ):
                    raise RuntimeError(
                        "API authentication or "
                        "permission error."
                    )

                if response.status_code >= 500:
                    if attempt == 0:
                        time.sleep(3)
                        continue

                raise RuntimeError(
                    f"API HTTP {response.status_code}: "
                    f"{response.text[:300]}"
                )

            except requests.RequestException as error:
                last_error = str(error)
                if attempt == 0:
                    time.sleep(3)
                    continue
                print(f"Network error: {error}")

    raise RuntimeError(
        f"All suitable models failed. "
        f"Last error: {last_error}"
    )


def main():
    if not API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY secret is missing."
        )

    print("AI Auto Post Bot Started")

    models = get_available_models()
    posts = []

    for topic in TOPICS:
        print(f"\nGenerating post: {topic}")

        content, model = generate_post(
            topic, models
        )

        posts.append({
            "topic": topic,
            "model": model,
            "content": content,
            "created_at": datetime.now(
                timezone.utc
            ).isoformat()
        })

        print(content)
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
