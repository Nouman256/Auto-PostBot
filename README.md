# TechVision Digital — Facebook + LinkedIn Auto Posting

This replacement workflow generates **two concepts per daily run**:
1. One technical/educational post about web development, WordPress, SEO, performance, security, or e-commerce.
2. One engagement post: original professional meme, question, poll, or relatable digital-business humor.

Each concept has separate LinkedIn and Facebook captions and separate images, so a normal daily run creates **4 platform posts and 4 image files**.

## Safety defaults

- `PUBLISH_LINKEDIN` and `PUBLISH_FACEBOOK` are `false` unless the GitHub repository variables explicitly enable them.
- By default, scheduled and manual runs are dry-run because both repository variables are set to `false`.
- A manual run publishes live only if `publish_live=true` **and** both repository variables `PUBLISH_LINKEDIN=true` and `PUBLISH_FACEBOOK=true`.
- After you deliberately set both variables to `true`, scheduled runs publish live automatically; the workflow checks history first and stops if a successful live run is already recorded for that UTC date.
- The workflow commits `post_history.json` back to the repository so the next run can avoid recent topics.
- The history key prevents duplicate history records; it is not a perfect API-level idempotency lock if a run crashes after publishing but before saving history. Check platform posts before manually retrying a failed live run.

## Repository files

Keep these files at the repository root:
- `generate_posts.py`
- `generate_images.py`
- `publish_linkedin.py`
- `publish_facebook.py`
- `record_history.py`
- `requirements.txt`
- `.github/workflows/social-auto-post.yml`

## GitHub setup

### 1. Add repository secrets

Repository → **Settings → Secrets and variables → Actions → New repository secret**:

- `GEMINI_API_KEY`
- `LINKEDIN_ACCESS_TOKEN`
- `FACEBOOK_PAGE_ID`
- `FACEBOOK_PAGE_ACCESS_TOKEN`

Never paste tokens into source code or commit them to Git.

### 2. Add repository variables

Repository → **Settings → Secrets and variables → Actions → Variables**:

- `PUBLISH_LINKEDIN` = `false`
- `PUBLISH_FACEBOOK` = `false`
- Optional `LINKEDIN_VERSION` = `202609`
- Optional `FACEBOOK_API_VERSION` = `v26.0`

The API versions are configurable; verify the versions and permissions available to your LinkedIn app and Meta app before live publishing.

### 3. Commit and enable Actions

Commit the files and push to the default branch. In GitHub, open **Actions** and enable workflows if GitHub asks.

### 4. First test: dry run

Actions → **TechVision Social Auto Posting** → Run workflow → leave `publish_live` unchecked.
Inspect the log and confirm:
- 2 concepts were generated (technical + engagement)
- both captions differ by platform
- all 4 images exist and match the concept
- both publishers report dry-run
- `post_history.json` is updated

The LinkedIn publisher performs a read-only `/v2/userinfo` check even during dry run, so a valid token is required. No posts are published while the publish flag is false.

### 5. Enable live publishing carefully

After a successful dry run:
1. Set both repository variables to `true`.
2. Run workflow manually with `publish_live` checked.
3. Confirm exactly two posts appeared on each platform.
4. If successful, decide whether to keep scheduled runs dry-run or modify the workflow's environment policy. As supplied, the scheduled event always sets publish flags to false intentionally.

**Important:** The daily scheduled workflow is deliberately dry-run. This prevents accidental publishing before you approve a live test. To enable unattended daily publishing after testing, replace each `PUBLISH_*` expression in the workflow with:
`${{ vars.PUBLISH_LINKEDIN == 'true' && 'true' || 'false' }}`
and
` ${{ vars.PUBLISH_FACEBOOK == 'true' && 'true' || 'false' }}`
respectively. Then the repository variables control scheduled publishing. Do this only after a successful manual live test.

## Schedule

The workflow starts once daily at **13:30 UTC (18:30 Pakistan Standard Time)**. GitHub Actions schedule timing is not guaranteed to start at the exact minute. Change the cron expression if needed. One workflow run creates and attempts to publish both post categories to both platforms.

## Design note

The graphics are custom Pillow-generated layouts with category-specific motifs and platform-specific copy. They are not generated photographic/AI images. If you want realistic laptop/device mockups or image-generation model artwork, that requires a separate image-generation API/service and its own credentials.

## Publishing caveats

- LinkedIn API access, scopes, product approval, token validity, and supported API version depend on your LinkedIn app.
- Meta Page publishing requires the correct Page access token, Page permissions, and API access.
- Test with dry-run first. Live publishing is an external side effect and can create public posts.
- The workflow runs in UTC for its daily deduplication key. If you change schedule timezone or run across UTC midnight, the daily key follows UTC date.
