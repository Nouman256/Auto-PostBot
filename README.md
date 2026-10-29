# TechVision Digital Social Auto-Post Bot

Generates one post concept per run and makes distinct LinkedIn/Facebook captions and images. Scheduled for **12:00 PM and 5:00 PM Pakistan time** (07:00 and 12:00 UTC).

## Repository files

Keep these files at the repository root and preserve `.github/workflows/social-auto-post.yml`:

- `generate_posts.py`
- `generate_images.py`
- `publish_linkedin.py`
- `publish_facebook.py`
- `record_history.py`
- `requirements.txt`
- `post_history.json` (create as `[]` if missing)

## GitHub Secrets

Repository → Settings → Secrets and variables → Actions → Secrets:

- `GEMINI_API_KEY`
- `LINKEDIN_ACCESS_TOKEN`
- `FACEBOOK_PAGE_ID`
- `FACEBOOK_PAGE_ACCESS_TOKEN`

Never put tokens in code or commit them.

## GitHub Variables

Repository → Settings → Secrets and variables → Actions → Variables:

- `PUBLISH_LINKEDIN` = `false`
- `PUBLISH_FACEBOOK` = `false`
- Optional `GEMINI_MODEL` = `gemini-2.5-flash`
- Optional `LINKEDIN_VERSION` = `202609` (use a version supported by your LinkedIn app)
- Optional `FACEBOOK_API_VERSION` = `v26.0` (use a version supported by your Meta app)

## Test first

1. Commit and push all files.
2. Open Actions → TechVision Social Auto Posting → Run workflow.
3. Choose `noon`, leave `publish_live` unchecked, and inspect logs/images.
4. Repeat for `evening`.
5. Only after the dry runs look right, set both publishing variables to `true` and run a manual test with `publish_live` checked.

Scheduled runs publish live only when both repository variables are `true`. Manual runs additionally require `publish_live=true`. If either variable is false, the publishers stay in dry-run mode.

## Notes

- GitHub scheduled jobs can start late; cron times are targets, not exact guarantees.
- The code records history after publisher steps. A crash after a platform accepts a post but before history is saved can still require checking the platform before retrying.
- LinkedIn and Meta API access, scopes, permissions, tokens, and supported API versions depend on your apps/accounts.
- `post_history.json` must be writable by the GitHub Actions bot; workflow permissions are set to `contents: write`.
