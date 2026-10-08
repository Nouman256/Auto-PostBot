
import os
import json
import requests
from datetime import datetime, timezone

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing")

MODEL = "gemini-2.5-flash"

URL = (
    "https://generativelanguage.googleapis.com/"
    f"v1beta/models/{MODEL}:generateContent"
)

TOPICS = [
    "Web Development",
    "Search Engine Optimization (SEO)",
    "Digital Marketing"
]

def generate_post(topic):
    prompt = f"""
You are an experienced digital marketing
and technology content creator.

Create one original, engaging social media
post about: {topic}.

Requirements:
- Write in English and Urdu.
- Include useful, practical advice.
- Use natural, professional language.
- Keep the content under 250 words.
- Include a compelling opening.
- Avoid exaggerated or unverified claims.
- Add 3 to 5 relevant hashtags.
- Do not repeat the same information
  in both languages unnecessarily.
- Return only the finished post.
"""

    response = requests.post(
        URL,
        headers={
            "x-goog-api-key": API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.8
            }
        },
        timeout=90
    )

    response.raise_for_status()

    data = response.json()

    return data["candidates"][0]["content"]["parts"][0]["text"]


def main():
    print("AI Auto Post Bot Started")

    posts = []

    for topic in TOPICS:
        print(f"Generating: {topic}")

        try:
            content = generate_post(topic)

            posts.append({
                "topic": topic,
                "content": content,
                "created_at": datetime.now(
                    timezone.utc
                ).isoformat()
            })

            print(content)
            print("-" * 50)

        except Exception as error:
            print(f"Failed for {topic}: {error}")
            raise

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

    print("All 3 posts generated successfully")


if __name__ == "__main__":
    main()
