AUTO POST BOT — SAFE CONTENT UPGRADE

Copy ONLY the four files in this ZIP's Post/ folder to the existing GitHub repository's Post/ directory:
Post/Bot.py, Post/Graphics.py, Post/Facebook.py, Post/LinkedIn.py

DO NOT change existing workflow YAML, schedules, GitHub Secrets, tokens, or social account settings.

Changes:
- One Gemini response contains distinct LinkedIn `content` and Facebook `facebook_content`.
- Two graphics: original generated_images/post_01.png for LinkedIn and generated_images/post_01_facebook.png for Facebook.
- Facebook publisher reads facebook_content and facebook_image_path, with fallback to legacy content and post_01.png.
- LinkedIn publisher uses same old content and image_path keys and identical existing upload/publish protocol.

TEST BEFORE MERGING:
1. Use a separate test branch so your scheduled workflow remains unaffected.
2. Inspect output JSON and both PNG images after running Bot.py and Graphics.py with POST_SLOT=web and valid GEMINI_API_KEY.
3. Run Facebook.py with PUBLISH_FACEBOOK=false; no real publication should occur.
4. Run LinkedIn.py with PUBLISH_LINKEDIN=false and LINKEDIN_ACCESS_TOKEN set; note the original dry-run still verifies account via network.
5. Review both captions and both images. Only then merge to main.

IMPORTANT: A dry-run cannot prove successful real publishing; publishing both channels live requires manual opt-in.
