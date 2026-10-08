
import os
import json
from pathlib import Path

import requests


# ======================================
# FACEBOOK CONFIGURATION
# ======================================

PAGE_ID = os.getenv(
    "FACEBOOK_PAGE_ID", ""
).strip()

PAGE_TOKEN = os.getenv(
    "FACEBOOK_PAGE_ACCESS_TOKEN", ""
).strip()

API_VERSION = os.getenv(
    "FACEBOOK_API_VERSION", "v26.0"
)

PUBLISH = os.getenv(
    "PUBLISH_FACEBOOK", "false"
).lower() == "true"

POST_FILE = Path("generated_posts.json")
IMAGE_FILE = Path("generated_images/post_01.png")


# ======================================
# LOAD GENERATED POST
# ======================================

def load_post():
    if not POST_FILE.exists():
        raise FileNotFoundError(
            "generated_posts.json is missing"
        )

    with POST_FILE.open(
        "r", encoding="utf-8"
    ) as file:
        posts = json.load(file)

    if not isinstance(posts, list) or not posts:
        raise ValueError(
            "No generated posts found"
        )

    caption = posts[0].get(
        "content", ""
    ).strip()

    if not caption:
        raise ValueError(
            "Facebook caption is empty"
        )

    if not IMAGE_FILE.is_file():
        raise FileNotFoundError(
            f"Image missing: {IMAGE_FILE}"
        )

    return caption


# ======================================
# PUBLISH FACEBOOK POST
# ======================================

def publish_facebook(caption):
    if not PAGE_ID:
        raise RuntimeError(
            "FACEBOOK_PAGE_ID is missing"
        )

    if not PAGE_TOKEN:
        raise RuntimeError(
            "FACEBOOK_PAGE_ACCESS_TOKEN is missing"
        )

    url = (
        f"https://graph.facebook.com/"
        f"{API_VERSION}/{PAGE_ID}/photos"
    )

    print("Publishing to TechVision Facebook Page...")

    with IMAGE_FILE.open("rb") as image:
        response = requests.post(
            url,
            data={
                "caption": caption,
                "published": "true"
            },
            files={
                "source": (
                    IMAGE_FILE.name,
                    image,
                    "image/png"
                )
            },
            headers={
                "Authorization": f"Bearer {PAGE_TOKEN}"
            },
            timeout=90
        )

    try:
        result = response.json()
    except ValueError:
        raise RuntimeError(
            "Facebook API returned invalid JSON"
        )

    if not response.ok or "id" not in result:
        error = result.get("error", {})

        raise RuntimeError(
            "Facebook publishing failed: "
            + str(
                error.get(
                    "message",
                    response.status_code
                )
            )
        )

    print("FACEBOOK POST PUBLISHED SUCCESSFULLY!")
    print("Facebook Photo ID:", result["id"])

    if result.get("post_id"):
        print(
            "Facebook Post ID:",
            result["post_id"]
        )


# ======================================
# MAIN
# ======================================

def main():
    print("Starting Facebook Auto Posting Bot")

    caption = load_post()

    print("Post prepared successfully")
    print("Caption length:", len(caption))
    print("Image:", IMAGE_FILE)

    # Safe manual testing
    if not PUBLISH:
        print("FACEBOOK DRY RUN SUCCESSFUL")
        print("No Facebook post published")
        return

    publish_facebook(caption)


if __name__ == "__main__":
    main()
