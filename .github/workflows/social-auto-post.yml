
import json
import os
import re
import hashlib
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

from google import genai

API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()

POST_FILE = Path("generated_posts.json")
HISTORY_FILE = Path("post_history.json")
TZ = ZoneInfo("Asia/Karachi")

SLOT = os.getenv("POST_SLOT", "").strip().lower()

if SLOT not in {"noon", "evening"}:
    now = datetime.now(TZ)
    SLOT = "noon" if now.hour < 14 else "evening"


PROMPTS = {
    "noon": """
Create ONE genuinely useful, specific, original educational social post
for a digital agency founder.

Topics can include SEO, guest posting, link building, WordPress,
web development, website speed, technical SEO, content strategy,
analytics, or digital business.

Requirements:
- Start with a strong hook.
- Teach a practical idea.
- Use short, readable paragraphs.
- Add a natural discussion question.
- Include 3-5 relevant hashtags.
- Do not invent statistics, case studies, personal experiences,
  guarantees, or sources.
- Avoid generic AI-sounding advice.

Brand signature:
— Muhammad Nouman | Founder & Team Head, TechVision Digital

Create DISTINCT versions for LinkedIn and Facebook.
LinkedIn should be professional and more detailed.
Facebook should be conversational and concise.

Create separate image headlines and subheadings for both platforms.
""",

    "evening": """
Create ONE engaging social post for a digital agency founder.

Use an interesting dilemma, relatable digital-work situation,
thoughtful question, mini-poll, or occasional light professional humor.

Topics can include SEO, guest posting, clients, WordPress,
web development, agency life, freelancing, digital business,
or online work.

Requirements:
- Encourage genuine comments.
- Include a clear question people can answer.
- Rotate formats and avoid repetitive generic prompts.
- Do not use rage bait, fake stories, or fabricated personal experience.
- Include 3-5 relevant hashtags.

Brand signature:
— Muhammad Nouman | Founder & Team Head, TechVision Digital

Create DISTINCT versions for LinkedIn and Facebook.
LinkedIn should be professional and discussion-led.
Facebook should be warmer, shorter, and more casual.

Create separate image headlines and subheadings for both platforms.
"""
}


def recent_topics():
    if not HISTORY_FILE.exists():
        return []

    try:
        data = json.loads(
            HISTORY_FILE.read_text(encoding="utf-8")
        )
    except (ValueError, OSError):
        return []

    if not isinstance(data, list):
        return []

    return [
        f"{item.get('title', '')} — {item.get('topic', '')}"
        for item in data[-40:]
        if isinstance(item, dict)
    ]


def extract_json(text):
    text = text.strip()
    text = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        text,
        flags=re.IGNORECASE
    )

    start = text.find("{")
    end = text.rfind("}")

    if start < 0 or end < start:
        raise ValueError(
            "Gemini response did not contain a JSON object."
        )

    return json.loads(text[start:end + 1])


def main():
    if not API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it in GitHub Secrets."
        )

    history = recent_topics()

    prompt = PROMPTS[SLOT]
    prompt += (
        "\n\nAvoid duplicating these recent topics/titles: "
        + json.dumps(history, ensure_ascii=False)
    )

    prompt += """
Return ONLY valid JSON with this exact structure:
{
  "title": "...",
  "topic": "...",
  "category": "technical or engagement",
  "linkedin_content": "...",
  "facebook_content": "...",
  "image_headline": "...",
  "image_subheading": "...",
  "facebook_image_headline": "...",
  "facebook_image_subheading": "..."
}

Keep all image headlines and subheadings concise and readable.
Use category "technical" for noon and "engagement" for evening.
Do not wrap the JSON in Markdown.
"""

    try:
        client = genai.Client(api_key=API_KEY)

        interaction = client.interactions.create(
            model=MODEL,
            input=prompt
        )

        generated_text = interaction.output_text

    except Exception as exc:
        raise RuntimeError(
            f"Gemini Interactions API failed using model {MODEL}: {exc}"
        ) from exc

    if not generated_text or not generated_text.strip():
        raise RuntimeError(
            "Gemini returned an empty response. Check your API key, "
            "model access, and API usage limits."
        )

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
        if not isinstance(post.get(field), str) or not post[field].strip():
            raise ValueError(
                f"Generated post is missing required field: {field}"
            )

    post["category"] = (
        "technical" if SLOT == "noon" else "engagement"
    )

    post["run_date"] = datetime.now(TZ).strftime("%Y-%m-%d")
    post["slot"] = SLOT

    post["dedupe_key"] = hashlib.sha256(
        f"{post['run_date']}|{SLOT}|{post['title']}".encode("utf-8")
    ).hexdigest()[:20]

    # Keep compatibility with scripts that read the "content" field.
    post["content"] = post["linkedin_content"]

    POST_FILE.write_text(
        json.dumps([post], ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"Generated {SLOT} post: {post['title']}")
    print("\nLINKEDIN PREVIEW\n")
    print(post["linkedin_content"])
    print("\nFACEBOOK PREVIEW\n")
    print(post["facebook_content"])


if __name__ == "__main__":
    main()
