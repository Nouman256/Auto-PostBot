import os
import json
from pathlib import Path
from datetime import datetime, timezone
import requests

TOKEN = os.getenv('LINKEDIN_ACCESS_TOKEN', '').strip()
VERSION = os.getenv('LINKEDIN_VERSION', '202609')
PUBLISH = os.getenv('PUBLISH_LINKEDIN', 'false').lower() == 'true'
API = 'https://api.linkedin.com'
if not TOKEN:
    raise RuntimeError('LINKEDIN_ACCESS_TOKEN missing')
HEADERS = {'Authorization': f'Bearer {TOKEN}', 'Linkedin-Version': VERSION,
           'X-Restli-Protocol-Version': '2.0.0', 'Accept': 'application/json'}

def check(response, action):
    if not response.ok:
        try:
            message = response.json().get('message', 'API error')
        except ValueError:
            message = response.text[:250]
        raise RuntimeError(f'{action} failed: HTTP {response.status_code} - {message}')

def author_urn():
    response = requests.get(f'{API}/v2/userinfo', headers={'Authorization': f'Bearer {TOKEN}', 'Accept': 'application/json'}, timeout=30)
    check(response, 'LinkedIn authentication')
    sub = response.json().get('sub')
    if not sub:
        raise RuntimeError('LinkedIn member ID missing')
    print('LinkedIn personal profile verified')
    return f'urn:li:person:{sub}'

def upload_image(author, path):
    response = requests.post(f'{API}/rest/images?action=initializeUpload',
        headers={**HEADERS, 'Content-Type': 'application/json'},
        json={'initializeUploadRequest': {'owner': author}}, timeout=30)
    check(response, 'Image initialization')
    value = response.json()['value']
    with open(path, 'rb') as file:
        uploaded = requests.put(value['uploadUrl'],
            headers={'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'image/png'},
            data=file, timeout=120)
    check(uploaded, 'Image upload')
    print('Image uploaded successfully')
    return value['image']

def publish(author, post):
    # LinkedIn's existing keys and publish mechanism remain unchanged.
    caption = post['content'].strip()
    path = Path(post['image_path'])
    if not path.is_file() or not 110 <= len(caption.split()) <= 260:
        raise RuntimeError('Missing image or invalid caption length')
    image_urn = upload_image(author, path)
    payload = {
        'author': author, 'commentary': caption, 'visibility': 'PUBLIC',
        'distribution': {'feedDistribution': 'MAIN_FEED', 'targetEntities': [], 'thirdPartyDistributionChannels': []},
        'content': {'media': {'id': image_urn, 'altText': post.get('image_subheading', 'Educational digital marketing graphic')}},
        'lifecycleState': 'PUBLISHED', 'isReshareDisabledByAuthor': False,
    }
    response = requests.post(f'{API}/rest/posts', headers={**HEADERS, 'Content-Type': 'application/json'}, json=payload, timeout=60)
    check(response, 'LinkedIn publishing')
    if response.status_code != 201:
        raise RuntimeError('Unexpected LinkedIn publishing response')
    post_id = response.headers.get('x-restli-id', '')
    print('LinkedIn post published successfully!')
    print('Post ID:', post_id)
    return post_id

def main():
    posts = json.loads(Path('generated_posts.json').read_text(encoding='utf-8'))
    if len(posts) != 1:
        raise RuntimeError('Expected exactly one post per scheduled run')
    post = posts[0]
    print('Topic:', post['topic'])
    print('Caption characters:', len(post['content']))
    print('Image:', post['image_path'])
    author = author_urn()
    if not PUBLISH:
        print('DRY RUN SUCCESSFUL - No LinkedIn post published')
        return
    post_id = publish(author, post)
    history_path = Path('post_history.json')
    history = json.loads(history_path.read_text(encoding='utf-8')) if history_path.exists() else []
    history.append({'title': post.get('title', post['image_headline']), 'topic': post['topic'],
                    'post_id': post_id, 'published_at': datetime.now(timezone.utc).isoformat()})
    history_path.write_text(json.dumps(history[-100:], ensure_ascii=False, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
