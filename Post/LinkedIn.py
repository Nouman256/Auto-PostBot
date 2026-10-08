
import os
import requests

ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")

if not ACCESS_TOKEN:
    raise RuntimeError(
        "LINKEDIN_ACCESS_TOKEN is missing"
    )

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "X-Restli-Protocol-Version": "2.0.0"
}


def test_linkedin():
    print("Testing LinkedIn API connection...")

    url = "https://api.linkedin.com/v2/me"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    if response.status_code == 200:
        print("LinkedIn connection successful!")
        print("Personal profile API accessible.")
    else:
        print(
            f"LinkedIn API returned HTTP "
            f"{response.status_code}"
        )
        print(response.text[:300])
        raise RuntimeError(
            "LinkedIn connection test failed."
        )


if __name__ == "__main__":
    test_linkedin()
