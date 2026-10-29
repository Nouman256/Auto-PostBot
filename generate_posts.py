
import json
import os
import re
import hashlib
import time
import random

from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

from google import genai


# =========================
# CONFIGURATION
# =========================

API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()

POST_FILE = Path("generated_posts.json")
HISTORY_FILE = Path("post_history.json")

TZ = ZoneInfo("Asia/Karachi")
MAX_ATTEMPTS = 4

SLOT = os.getenv("POST_SLOT", "").strip().lower()

if SLOT not in {"noon", "evening"}:
    current_time = datetime.now(TZ)
    SLOT = "noon" if current_time.hour < 14 else "evening"


# =========================
# POST PROMPTS
# =========================

PROMPTS = {
    "noon": """
Create ONE useful, original educational social media post
for a professional digital agency founder.

Possible topics:
SEO, guest posting, link building, WordPress, web development,
website speed, technical SEO, content strategy, analytics,
website maintenance, and digital business.

Requirements:
- Start with a strong hook.
- Explain one practical idea clearly.
- Use short, readable paragraphs.
- End with a natural discussion question.
- Include 3-5 relevant hashtags.
- Do not invent statistics, case studies, sources, or personal experiences.
- Avoid repetitive, generic AI-sounding advice.
- Do not promise guaranteed rankings or performance results.

Brand signature:
— Muhammad Nouman | Founder & Team Head, TechVision Digital

Create distinct versions for LinkedIn and Facebook.
LinkedIn should be professional and informative.
Facebook should be conversational and concise.

Create separate image headlines and subheadings for both platforms.
""",

    "evening": """
Create ONE engaging social media post for a digital agency founder.

Possible formats:
- An interesting industry question
- A relatable digital-work situation
- A professional mini-poll
- A thoughtful business dilemma
- Occasional light professional humor

Possible topics:
SEO, guest posting, clients, WordPress, web development,
agency life, freelancing, content creation, and digital business.

Requirements:
- Encourage genuine comments.
- Ask a clear question people can answer.
- Vary the format and topic.
- Do not invent personal stories or fake results.
- Avoid rage bait and engagement manipulation.
- Include 3-5 relevant hashtags.

Brand signature:
— Muhammad Nouman | Founder & Team Head, TechVision Digital

Create distinct versions for LinkedIn and Facebook.
LinkedIn should be professional and discussion-led.
Facebook should be warmer, shorter, and more casual.

Create separate image headlines and subheadings for both platforms.
"""
}


# =========================
# READ RECENT POST HISTORY
# =========================

def recent_topics():
    if not HISTORY_FILE.exists():
        return []

    try:
        data = json.loads(
            HISTORY_FILE.read_text(encoding="utf-8")
        )
    except (ValueError, OSError):
        print("Warning: Could not read post history.")
        return []

    if not isinstance(data, list):
        return []

    topics = []

    for item in data[-40:]:
        if isinstance(item, dict):
            title = item.get("title", "")
            topic = item.get("topic", "")
            topics.append(f"{title} — {topic}")

    return topics


# =========================
# EXTRACT JSON FROM RESPONSE
# =========================

def extract_json(response_text):
    response_text = response_text.strip()

    response_text = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        response_text,
        flags=re.IGNORECASE
    )

    start = response_text.find("{")
    end = response_text.rfind("}")

    if start == -1 or end == -1 or end < start:
        raise ValueError(
            "Gemini response did not contain a valid JSON object."
        )

    try:
        return json.loads(response_text[start:end + 1])
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Could not parse Gemini JSON response: {exc}"
        ) from exc


# =========================
# GENERATE CONTENT WITH RETRIES
# =========================

def generate_with_retry(client, prompt):
    last_error = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            print(
                f"Connecting to Gemini API "
                f"(attempt {attempt}/{MAX_ATTEMPTS})..."
            )

            interaction = client.interactions.create(
                model=MODEL,
                input=prompt
            )

            generated_text = interaction.output_text

            if not generated_text or not generated_text.strip():
                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            print("Gemini response received successfully.")
            return generated_text

        except Exception as exc:
            last_error = exc
            error_text = str(exc).lower()

            # Do not retry errors that usually require a configuration fix.
            permanent_indicators = (
                " 400 ",
                " 401 ",
                " 403 ",
                " 404 ",
                "invalid api key",
                "api key not valid",
                "permission denied",
                "unauthenticated",
                "not found",
                "unsupported model",
            )

            if any(
                indicator in f" {error_text} "
                for indicator in permanent_indicators
            ):
                raise RuntimeError(
                    f"Gemini returned a non-retryable error. "
                    f"Check the model name, API key, and API access. "
                    f"Details: {exc}"
                ) from exc

            if attempt == MAX_ATTEMPTS:
                break

            wait_seconds = (2 ** attempt) + random.uniform(0, 1)

            print(
                f"Gemini request failed: "
                f"{type(exc).__name__}: {exc}"
            )
            print(
                f"Retrying in {wait_seconds:.1f} seconds..."
            )

            time.sleep(wait_seconds)

    raise RuntimeError(
        f"Gemini API failed after {MAX_ATTEMPTS} attempts. "
        f"Model: {MODEL}. Last error: {last_error}"
    ) from last_error


# =========================
# MAIN
# =========================

def main():
    if not API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. "
            "Add it under GitHub Settings > Secrets and variables > Actions."
        )

    print("=" * 50)
    print("TechVision Digital Social Post Generator")
    print("Pakistan time:", datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S"))
    print("Post slot:", SLOT)
    print("Gemini model:", MODEL)
    print("=" * 50)

    history = recent_topics()

    prompt = PROMPTS[SLOT]

    prompt += (
        "\n\nAvoid repeating these recent topics/titles: "
        + json.dumps(history, ensure_ascii=False)
    )

    prompt += """

Return ONLY one valid JSON object using this exact structure:

{
  "title": "Short internal post title",
  "topic": "Specific topic",
  "category": "technical or engagement",
  "linkedin_content": "Complete LinkedIn caption",
  "facebook_content": "Complete Facebook caption",
  "image_headline": "LinkedIn image headline",
  "image_subheading": "LinkedIn image subheading",
  "facebook_image_headline": "Facebook image headline",
  "facebook_image_subheading": "Facebook image subheading"
}

Rules:
- All nine fields must be strings.
- Do not wrap the JSON in Markdown.
- Keep image headlines short and readable.
- Make LinkedIn and Facebook captions meaningfully different.
- Do not invent statistics or claim personal experience.
- For the noon slot, category must be technical.
- For the evening slot, category must be engagement.
"""

    client = genai.Client(api_key=API_KEY)

    generated_text = generate_with_retry(client, prompt)
    post = extract_json(generated_text)

    required_fields = [
        "title",
        "topic",
        "category",
        "linkedin_content",
        "facebook_content",
        "image_headline",
        "image_subheading",
        "facebook_image_headline",
        "facebook_image_subheading",
    ]

    for field in required_fields:
        value = post.get(field)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"Generated post is missing a valid field: {field}"
            )

    # Enforce the category according to the scheduled slot.
    post["category"] = (
        "technical" if SLOT == "noon" else "engagement"
    )

    post["run_date"] = datetime.now(TZ).strftime("%Y-%m-%d")
    post["slot"] = SLOT

    post["dedupe_key"] = hashlib.sha256(
        f"{post['run_date']}|{SLOT}|{post['title']}".encode("utf-8")
    ).hexdigest()[:20]

    # Keep compatibility with scripts that use the content field.
    post["content"] = post["linkedin_content"]

    # The image generator can add image paths in a later step.
    POST_FILE.write_text(
        json.dumps([post], ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("\nPost generated successfully.")
    print("Title:", post["title"])
    print("Topic:", post["topic"])
    print("Slot:", post["slot"])

    print("\n========== LINKEDIN PREVIEW ==========\n")
    print(post["linkedin_content"])

    print("\n========== FACEBOOK PREVIEW ==========\n")
    print(post["facebook_content"])

    print(f"\nSaved to: {POST_FILE}")


if __name__ == "__main__":
    main()
