import json, os
from pathlib import Path
import requests
TOKEN=os.getenv('LINKEDIN_ACCESS_TOKEN','').strip(); VERSION=os.getenv('LINKEDIN_VERSION','202609').strip(); PUBLISH=os.getenv('PUBLISH_LINKEDIN','false').lower()=='true'
API='https://api.linkedin.com'; FILE=Path('generated_posts.json')
HEADERS={'Authorization':f'Bearer {TOKEN}','Linkedin-Version':VERSION,'X-Restli-Protocol-Version':'2.0.0','Accept':'application/json'}
def check(r,action):
    if not r.ok:
        try: msg=r.json().get('message','API error')
        except ValueError: msg=r.text[:250]
        raise RuntimeError(f'{action} failed: HTTP {r.status_code} - {msg}')
def author_urn():
    r=requests.get(f'{API}/v2/userinfo',headers={'Authorization':f'Bearer {TOKEN}','Accept':'application/json'},timeout=30); check(r,'LinkedIn authentication')
    sub=r.json().get('sub')
    if not sub: raise RuntimeError('LinkedIn member ID missing')
    return f'urn:li:person:{sub}'
def upload_image(author,path):
    r=requests.post(f'{API}/rest/images?action=initializeUpload',headers={**HEADERS,'Content-Type':'application/json'},json={'initializeUploadRequest':{'owner':author}},timeout=30); check(r,'Image initialization')
    val=r.json()['value']
    with open(path,'rb') as f: up=requests.put(val['uploadUrl'],headers={'Authorization':f'Bearer {TOKEN}','Content-Type':'image/png'},data=f,timeout=120)
    check(up,'Image upload'); return val['image']
def publish_one(author,p):
    path=Path(p['image_path'])
    if not path.is_file(): raise FileNotFoundError(f'LinkedIn image missing: {path}')
    image=upload_image(author,path)
    payload={'author':author,'commentary':p['linkedin_content'].strip(),'visibility':'PUBLIC','distribution':{'feedDistribution':'MAIN_FEED','targetEntities':[],'thirdPartyDistributionChannels':[]},'content':{'media':{'id':image,'altText':p.get('image_subheading','TechVision Digital post graphic')}},'lifecycleState':'PUBLISHED','isReshareDisabledByAuthor':False}
    r=requests.post(f'{API}/rest/posts',headers={**HEADERS,'Content-Type':'application/json'},json=payload,timeout=60); check(r,'LinkedIn publishing')
    if r.status_code not in (200,201): raise RuntimeError(f'Unexpected LinkedIn response: {r.status_code}')
    return r.headers.get('x-restli-id','')
def main():
    if not TOKEN: raise RuntimeError('LINKEDIN_ACCESS_TOKEN missing')
    posts=json.loads(FILE.read_text(encoding='utf-8'))
    if not PUBLISH:
        for p in posts: print(f"LINKEDIN DRY RUN [{p['category']}]: {p['title']} | image={p.get('image_path')}")
        return
    author=author_urn()
    for p in posts:
        p['_linkedin_post_id']=publish_one(author,p); print('LinkedIn published:',p['_linkedin_post_id'])
    FILE.write_text(json.dumps(posts,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__': main()
