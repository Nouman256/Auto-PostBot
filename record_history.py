import json, hashlib
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
POST=Path('generated_posts.json'); HIST=Path('post_history.json'); TZ=ZoneInfo('Asia/Karachi')
def main():
    posts=json.loads(POST.read_text(encoding='utf-8'))
    try: history=json.loads(HIST.read_text(encoding='utf-8')) if HIST.exists() else []
    except (ValueError,OSError): history=[]
    if not isinstance(history,list): history=[]
    seen={x.get('dedupe_key') for x in history if isinstance(x,dict)}
    now=datetime.now(TZ).isoformat()
    for p in posts:
        key=p.get('dedupe_key') or hashlib.sha256(f"{p.get('run_date')}|{p.get('slot')}|{p.get('title')}".encode()).hexdigest()[:20]
        if key in seen: print('History already contains:',key); continue
        li=p.get('_linkedin_post_id',''); fb=p.get('_facebook_post_id','')
        history.append({'title':p.get('title',''),'topic':p.get('topic',''),'category':p.get('category',''),'slot':p.get('slot',''),'run_date':p.get('run_date',''),'dedupe_key':key,'linkedin_post_id':li,'facebook_post_id':fb,'published_at':now,'mode':'published' if li or fb else 'dry_run'})
        seen.add(key)
    HIST.write_text(json.dumps(history[-500:],ensure_ascii=False,indent=2),encoding='utf-8'); print(f'History saved: {min(len(history),500)} records')
if __name__=='__main__': main()
