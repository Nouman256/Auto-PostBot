
import os
import requests

ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")


def test_linkedin():
    print("Starting LinkedIn API connection test...")

    if not ACCESS_TOKEN:
        raise RuntimeError(
            "LINKEDIN_ACCESS_TOKEN is missing."
        )

    url = "https://api.linkedin.com/v2/userinfo"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        if response.status_code != 200:
            print(
                "LinkedIn API returned HTTP",
                response.status_code
            )
            raise RuntimeError(
                "LinkedIn authentication failed. "
                "Check OAuth permissions and token."
            )

        data = response.json()

        member_id = data.get("sub")

        if not member_id:
            raise RuntimeError(
                "LinkedIn member ID not found."
            )

        print("LinkedIn API connection successful!")
        print("Member ID:", member_id)
        print("Author URN:", f"urn:li:person:{member_id}")
        print("Personal profile identification complete.")
        print("No LinkedIn post has been published.")

    except requests.RequestException as error:
        raise RuntimeError(
            "LinkedIn API request failed."
        ) from error


if __name__ == "__main__":
    test_linkedin()
