
import os
import json
from pathlib import Path

import requests


# ======================================
# LINKEDIN CONFIGURATION
# ======================================

ACCESS_TOKEN = os.getenv(
    "LINKEDIN_ACCESS_TOKEN", ""
).strip()

LINKEDIN_VERSION = os.getenv(
    "LINKEDIN_VERSION", "202610"
)

PUBLISH = os.getenv(
    "PUBLISH_LINKEDIN", "false"
).lower() == "true"

API_URL = "https://api.linkedin.com"

if not ACCESS_TOKEN:
    raise RuntimeError(
        "LINKEDIN_ACCESS_TOKEN is missing."
    )

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Linkedin-Version": LINKEDIN_VERSION,
    "X-Restli-Protocol-Version": "2.0.0",
    "Accept": "application/json",
}


# ======================================
# API ERROR HANDLING
# ======================================

def check_response(response, action):
    if response.ok:
        return

    try:
        error_data = response.json()
        message = error_data.get(
            "message", "Unknown API error"
        )
    except ValueError:
        message = "API request failed"

    raise RuntimeError(
        f"{action} failed: "
        f"HTTP {response.status_code} - {message}"
    )


# ======================================
# GET LINKEDIN MEMBER ID
# ======================================

def get_linkedin_author():
    print("Connecting to LinkedIn API...")

    response = requests.get(
        f"{API_URL}/v2/userinfo",
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Accept": "application/json",
        },
        timeout=30,
    )

    check_response(
        response, "LinkedIn authentication"
    )

    member_id = response.json().get("sub")

    if not member_id:
        raise RuntimeError(
            "LinkedIn Member ID not found."
        )

    print("LinkedIn API connection successful!")
    print("Personal profile verified.")

    return f"urn:li:person:{member_id}"


# ======================================
# LOAD GENERATED POSTS
# ======================================

def load_posts():
    file_path = Path("generated_posts.json")

    if not file_path.exists():
        raise RuntimeError(
            "generated_posts.json not found."
        )

    with open(
        file_path, "r", encoding="utf-8"
    ) as file:
        data = json.load(file)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in (
            "posts",
            "generated_posts",
        ):
            if isinstance(data.get(key), list):
                return data[key]

        return [data]

    raise RuntimeError(
        "Invalid generated_posts.json format."
    )


# ======================================
# EXTRACT POST CAPTION
# ======================================

def get_caption(post):
    if isinstance(post, str):
        return post.strip()

    if not isinstance(post, dict):
        return ""

    for key in (
        "linkedin_caption",
        "caption",
        "content",
        "post",
        "text",
    ):
        value = post.get(key)

        if isinstance(value, str):
            if value.strip():
                return value.strip()

    parts = []

    for key in (
        "title",
        "heading",
        "english",
        "urdu",
        "english_caption",
        "urdu_caption",
        "hashtags",
    ):
        value = post.get(key)

        if isinstance(value, list):
            value = " ".join(
                str(item) for item in value
            )

        if isinstance(value, str):
            if value.strip():
                parts.append(value.strip())

    return "\n\n".join(parts)


# ======================================
# FIND GENERATED IMAGE
# ======================================

def get_image(post, index):
    candidates = []

    if isinstance(post, dict):
        for key in (
            "image_path",
            "image",
            "graphic_path",
        ):
            value = post.get(key)

            if isinstance(value, str):
                candidates.append(Path(value))

    candidates.extend([
        Path(
            f"generated_images/post_{index:02d}.png"
        ),
        Path(
            f"generated_images/post_{index}.png"
        ),
    ])

    for image_path in candidates:
        if image_path.is_file():
            return image_path

    return None


# ======================================
# UPLOAD IMAGE TO LINKEDIN
# ======================================

def upload_image(author, image_path):
    print("Initializing LinkedIn image upload...")

    response = requests.post(
        f"{API_URL}/rest/images?action=initializeUpload",
        headers={
            **HEADERS,
            "Content-Type": "application/json",
        },
        json={
            "initializeUploadRequest": {
                "owner": author
            }
        },
        timeout=30,
    )

    check_response(
        response, "Image initialization"
    )

    upload_data = response.json()["value"]

    upload_url = upload_data["uploadUrl"]
    image_urn = upload_data["image"]

    print("Uploading premium graphic...")

    with open(image_path, "rb") as image_file:
        response = requests.put(
            upload_url,
            headers={
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "image/png",
            },
            data=image_file,
            timeout=120,
        )

    check_response(
        response, "Image upload"
    )

    print("Image uploaded successfully!")

    return image_urn


# ======================================
# PUBLISH LINKEDIN POST
# ======================================

def publish_post(author, caption, image_path):
    print("Preparing LinkedIn post...")

    image_urn = upload_image(
        author, image_path
    )

    payload = {
        "author": author,
        "commentary": caption,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "content": {
            "media": {
                "id": image_urn,
                "altText": (
                    "Digital marketing educational graphic"
                ),
            }
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    print("Publishing to LinkedIn...")

    response = requests.post(
        f"{API_URL}/rest/posts",
        headers={
            **HEADERS,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )

    check_response(
        response, "LinkedIn publishing"
    )

    if response.status_code != 201:
        raise RuntimeError(
            "Unexpected LinkedIn publishing response."
        )

    post_id = response.headers.get(
        "x-restli-id", "Not returned"
    )

    print("LinkedIn post published successfully!")
    print("Post ID:", post_id)


# ======================================
# MAIN BOT
# ======================================

def main():
    print("================================")
    print("LINKEDIN AUTO POST BOT")
    print("================================")

    author = get_linkedin_author()

    posts = load_posts()

    print("Generated posts:", len(posts))

    if not posts:
        raise RuntimeError(
            "No generated posts available."
        )

    # Publish only one post per run
    selected_post = posts[0]

    caption = get_caption(selected_post)

    image_path = get_image(
        selected_post, 1
    )

    if not caption:
        raise RuntimeError(
            "Caption not found in generated posts."
        )

    if not image_path:
        raise RuntimeError(
            "Generated image not found."
        )

    print("Caption ready.")
    print("Caption characters:", len(caption))
    print("Image ready:", image_path)

    # Safety: no publishing during dry run
    if not PUBLISH:
        print("================================")
        print("DRY RUN SUCCESSFUL")
        print("No LinkedIn post published.")
        print("================================")
        return

    publish_post(
        author,
        caption,
        image_path,
    )

    print("================================")
    print("LINKEDIN PUBLISHING COMPLETE")
    print("================================")


if __name__ == "__main__":
    main()
