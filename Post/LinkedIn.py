
import os
import requests

ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")


def test_linkedin():
    print("Checking LinkedIn configuration...")

    if not ACCESS_TOKEN:
        raise RuntimeError(
            "LINKEDIN_ACCESS_TOKEN is missing."
        )

    print("LinkedIn access token is configured.")
    print("Checking token with LinkedIn API...")

    url = "https://api.linkedin.com/v2/userinfo"

    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        },
        timeout=30
    )

    if response.status_code == 200:
        print("LinkedIn userinfo request successful.")
    elif response.status_code == 403:
        print(
            "Userinfo permission is not available. "
            "This does not prove posting access failed."
        )
    elif response.status_code == 401:
        raise RuntimeError(
            "LinkedIn token is invalid or expired."
        )
    else:
        raise RuntimeError(
            f"LinkedIn returned HTTP "
            f"{response.status_code}"
        )

    print("No LinkedIn post was published.")


if __name__ == "__main__":
    test_linkedin()
