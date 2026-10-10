import os
import json
from pathlib import Path
import requests

PAGE_ID = os.getenv('FACEBOOK_PAGE_ID', '').strip()
PAGE_TOKEN = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN', '').strip()
API_VERSION = os.getenv('FACEBOOK_API_VERSION', 'v26.0')
PUBLISH = os.getenv('PUBLISH_FACEBOOK', 'false').lower() == 'true'
POST_FILE = Path('generated_posts.json')
DEFAULT_IMAGE_FILE = Path('generated_images/post_01.png')


def load_post():
    if not POST_FILE.exists():
        raise FileNotFoundError('generated_posts.json is missing')
    with POST_FILE.open('r', encoding='utf-8') as file:
        posts = json.load(file)
    if not isinstance(posts, list) or not posts:
        raise ValueError('No generated posts found')
    post = posts[0]
    # Prefer Facebook-specific copy, preserving the old single-caption format as a fallback.
    caption = (post.get('facebook_content') or post.get('content') or '').strip()
    if not caption:
        raise ValueError('Facebook caption is empty')
    image_path = Path(post.get('facebook_image_path') or str(DEFAULT_IMAGE_FILE))
    if not image_path.is_file():
        raise FileNotFoundError(f'Image missing: {image_path}')
    return caption, image_path


def publish_facebook(caption, image_path):
    if not PAGE_ID:
        raise RuntimeError('FACEBOOK_PAGE_ID is missing')
    if not PAGE_TOKEN:
        raise RuntimeError('FACEBOOK_PAGE_ACCESS_TOKEN is missing')
    url = f'https://graph.facebook.com/{API_VERSION}/{PAGE_ID}/photos'
    print('Publishing to TechVision Facebook Page...')
    with image_path.open('rb') as image:
        response = requests.post(
            url,
            data={'caption': caption, 'published': 'true'},
            files={'source': (image_path.name, image, 'image/png')},
            headers={'Authorization': f'Bearer {PAGE_TOKEN}'},
            timeout=90,
        )
    try:
        result = response.json()
    except ValueError:
        raise RuntimeError('Facebook API returned invalid JSON')
    if not response.ok or 'id' not in result:
        error = result.get('error', {})
        raise RuntimeError('Facebook publishing failed: ' + str(error.get('message', response.status_code)))
    print('FACEBOOK POST PUBLISHED SUCCESSFULLY!')
    print('Facebook Photo ID:', result['id'])
    if result.get('post_id'):
        print('Facebook Post ID:', result['post_id'])


def main():
    print('Starting Facebook Auto Posting Bot')
    caption, image_path = load_post()
    print('Post prepared successfully')
    print('Caption length:', len(caption))
    print('Image:', image_path)
    if not PUBLISH:
        print('FACEBOOK DRY RUN SUCCESSFUL')
        print('No Facebook post published')
        return
    publish_facebook(caption, image_path)


if __name__ == '__main__':
    main()
