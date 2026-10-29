import json, os
from pathlib import Path
import requests
PAGE_ID=os.getenv('FACEBOOK_PAGE_ID','').strip(); TOKEN=os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN','').strip(); VERSION=os.getenv('FACEBOOK_API_VERSION','v26.0').strip(); PUBLISH=os.getenv('PUBLISH_FACEBOOK','false').lower()=='true'; FILE=Path('generated_posts.json')
def publish_one(p):
    path=Path(p['facebook_image_path'])
    if not path.is_file(): raise FileNotFoundError(f'Facebook image missing: {path}')
    url=f'https://graph.facebook.com/{VERSION}/{PAGE_ID}/photos'
    with path.open('rb') as image:
        r=requests.post(url,data={'caption':p['facebook_content'].strip(),'published':'true'},files={'source':(path.name,image,'image/png')},headers={'Authorization':f'Bearer {TOKEN}'},timeout=90)
    try: data=r.json()
    except ValueError: raise RuntimeError('Facebook API returned invalid JSON')
    if not r.ok or 'id' not in data: raise RuntimeError(f"Facebook publishing failed: {data.get('error',{}).get('message',r.status_code)}")
    return data.get('post_id') or data['id']
def main():
    posts=json.loads(FILE.read_text(encoding='utf-8'))
    if not PAGE_ID or not TOKEN: raise RuntimeError('FACEBOOK_PAGE_ID or FACEBOOK_PAGE_ACCESS_TOKEN missing')
    if not PUBLISH:
        for p in posts: print(f"FACEBOOK DRY RUN [{p['category']}]: {p['title']} | image={p.get('facebook_image_path')}")
        return
    for p in posts: p['_facebook_post_id']=publish_one(p); print('Facebook published:',p['_facebook_post_id'])
    FILE.write_text(json.dumps(posts,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__': main()
