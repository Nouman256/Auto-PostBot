# Auto Post Bot

An automated social posting workflow that uses Gemini to prepare **different professional captions and graphics for LinkedIn and Facebook**. It runs through GitHub Actions on the existing schedule, with optional manual runs.

## What changed in the content upgrade

- LinkedIn receives a professional B2B caption with a useful hook, practical insight, and a tidy list when appropriate.
- Facebook receives a **separately written** approachable, professional caption. It is not simply a copy of the LinkedIn post.
- Both platforms receive their **own square 1080 × 1080 PNG graphic** with topic-specific headline, supporting copy, and clean design.
- Existing publishing APIs, environment variable names, cron schedule, and manual publish switches remain unchanged.
- These changes improve content formatting and graphic layout, not image generation through an external AI image service: graphics are drawn locally with Pillow.

## Project files

| File | Purpose |
| --- | --- |
| `Post/Bot.py` | Selects topic, calls Gemini with retry/model fallback, validates two captions and graphic copy, writes `generated_posts.json` |
| `Post/Graphics.py` | Creates the two PNG graphics and adds their paths to the generated JSON |
| `Post/LinkedIn.py` | Publishes LinkedIn-specific `content` and `image_path`; records successful LinkedIn posts in history |
| `Post/Facebook.py` | Publishes `facebook_content` and `facebook_image_path`, with fallback to the previous keys |
| `.github/workflows/<your-existing-workflow>.yml` | Schedules generation and runs both publishers; **keep the existing workflow unchanged** |

## Existing schedule (Pakistan Standard Time, UTC+5)

| UTC cron | Pakistan time | Topic / slot |
| --- | --- | --- |
| `7 3 * * *` | 8:07 AM | Web Development (`web`) |
| `7 11 * * *` | 4:07 PM | Search Engine Optimization (`seo`) |
| `7 19 * * *` | 12:07 AM (next local calendar day) | Digital Marketing (`marketing`) |

GitHub Actions scheduled starts may be delayed by GitHub; the cron fields themselves have not been altered.

## Setup and secrets

Python 3.11. Dependencies: `requests`, `Pillow` (installed in the existing workflow).

The existing repository secrets must remain configured:

- `GEMINI_API_KEY`
- `LINKEDIN_ACCESS_TOKEN`
- `FACEBOOK_PAGE_ID`
- `FACEBOOK_PAGE_ACCESS_TOKEN`

The existing workflow also passes `LINKEDIN_VERSION` (currently `202609`) and `FACEBOOK_API_VERSION` (currently `v26.0`). Do not commit any secret or access token into source code.

## Generated output

Each run creates one entry in `generated_posts.json` with these relevant keys:

- `content`: LinkedIn caption (legacy key retained)
- `image_headline`, `image_subheading`: LinkedIn graphic copy
- `image_path`: LinkedIn graphic path, typically `generated_images/post_01.png`
- `facebook_content`: independently generated Facebook caption
- `facebook_image_headline`, `facebook_image_subheading`: Facebook graphic copy
- `facebook_image_path`: Facebook graphic path, typically `generated_images/post_01_facebook.png`
- `topic`, `title`, `slot`, `model`, `created_at`: metadata

These are generated outputs, not files to edit by hand before scheduled runs.

## Manual dry-run test (before going live)

1. Back up your currently working branch and test the new Python files on a separate branch. Do **not** edit workflow YAML, tokens, cron times, or API endpoints.
2. Install dependencies: `pip install requests Pillow`.
3. Set `GEMINI_API_KEY` and `POST_SLOT=web` in your environment, then run `python Post/Bot.py`.
4. Run `python Post/Graphics.py`. Check `generated_posts.json` and inspect both PNG files. Confirm captions are distinct and neither image clips its text.
5. For a **local** Facebook dry run, set `PUBLISH_FACEBOOK=false`, then run `python Post/Facebook.py`.
6. For a **local** LinkedIn dry run, set `LINKEDIN_ACCESS_TOKEN` and `PUBLISH_LINKEDIN=false`, then run `python Post/LinkedIn.py`. **Important:** the existing LinkedIn dry run still calls LinkedIn's `/v2/userinfo` to verify the account; it does not publish.
7. Only after reviewing results, merge to the live branch. You can use **Actions → Auto Post Bot → Run workflow** with both publish switches **off** for a generation-only check; inspect its uploaded artifacts.

### Publishing behavior

- Scheduled workflow runs set both publishing switches to true, as before.
- Manual `workflow_dispatch` defaults both publishing switches to false. Set one or both to true only when ready to post for real.
- The workflow's LinkedIn step runs before Facebook. A failure may prevent later steps from running. This existing behavior has not been changed.
- A successful dry run **does not prove** live API publication works. Review logs of an explicitly enabled manual publication before relying on the next scheduled run.
- The existing history is updated after a successful LinkedIn publish; do not assume it is a record of Facebook posting.

## Rollback

If output quality, formatting, or publishing is not right, restore the four previous `Post/*.py` files from your backup/previous commit. Keep the same workflow and secrets. This reverts the content upgrade without reconfiguring the accounts.

## Scope of this upgrade

The aim is to improve post quality and make the Facebook/LinkedIn content separate **without interrupting the previously working automation**. Live publication, account permissions, and exact timing still need verification in your own GitHub Actions run.

## V3 visual redesign (October 2026)

This release **replaces the old static boxed graphic** with a new Pillow-generated composition. The 1080×1080 artwork includes a branded top strip (typographic TechVision mark, not an official logo), a prominent dynamic headline, one useful takeaway, a subject-specific illustration (web interface / search results / marketing chart), and three AI-written visual action points. The two platforms get separate copy and image files. No image-generation API or new Python dependencies are required.

| File | Responsibility |
| --- | --- |
| `Post/Bot.py` | Generates different Facebook / LinkedIn captions, image headlines, and three visual points per platform through Gemini; existing retry and schedule inputs are preserved. |
| `Post/Graphics.py` | Renders two visually distinct square images with dynamic content; writes `image_path` and `facebook_image_path`. |
| `Post/LinkedIn.py` | Existing LinkedIn image-upload and publishing path; reads `content` and `image_path`. |
| `Post/Facebook.py` | Existing Facebook photo API path; reads `facebook_content` and `facebook_image_path`, with legacy fallback. |

### Upgrade safely

1. Keep a copy of the existing working files or create a backup Git branch.
2. Replace the four files in the repository's `Post/` folder. Do **not** replace or modify the current GitHub Actions workflow / Secrets.
3. In **Actions → Auto Post Bot → Run workflow**, leave **Publish LinkedIn** and **Publish Facebook** unchecked. Choose a topic and run.
4. Download the `premium-social-content` artifact. Inspect the captions in `generated_posts.json` and both PNG files in `generated_images/`.
5. If approved, use a manual run with publishing enabled for one platform at a time. Note that a real publish may create public posts; verify image and caption before enabling it.
6. The existing cron runs will continue to publish automatically after the files are merged to the scheduled branch. Restore the backup branch if the content fails review.

The **new generator requires** `linkedin_visual_points` and `facebook_visual_points` to each be an array of three 3–38-character strings. It rejects incomplete Gemini JSON rather than silently producing misleading labels. This means malformed AI responses can fail a run; review the Actions log instead of assuming a post went live. Existing `post_history.json` and account setup are unchanged.

### Local graphics-only test (no social publishing)

From the repository root, ensure `generated_posts.json` is present, then run:

```bash
python Post/Graphics.py
```

This creates `generated_images/post_01.png` (LinkedIn) and `generated_images/post_01_facebook.png` (Facebook) and updates their paths in JSON. Test-generated files from this package are demonstration samples, not customer posts.
