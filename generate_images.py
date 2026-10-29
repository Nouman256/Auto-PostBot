import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SIZE = 1080
OUT = Path('generated_images'); OUT.mkdir(exist_ok=True)
FONT_DIRS = [Path('/usr/share/fonts/truetype/dejavu'), Path('/usr/share/fonts/truetype/liberation2')]
FONT_DIR = next((p for p in FONT_DIRS if p.exists()), FONT_DIRS[0])
PALETTE = {'technical': ('#67D7FF', '#132239', 'TECHVISION / TECH INSIGHTS'), 'engagement': ('#FFC66D', '#24203A', 'TECHVISION / COMMUNITY')}
def font(size, bold=False):
    names = ['DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf', 'LiberationSans-Bold.ttf' if bold else 'LiberationSans-Regular.ttf']
    for directory in FONT_DIRS:
        for name in names:
            path = directory / name
            if path.exists(): return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()
def wrap(draw, text, width, size, bold=False):
    f = font(size, bold); lines=[]; current=''
    for word in text.split():
        candidate=(current+' '+word).strip()
        if draw.textbbox((0,0), candidate, font=f)[2] <= width: current=candidate
        else:
            if current: lines.append(current)
            current=word
    if current: lines.append(current)
    return lines
def make(post, platform, index):
    category=post['category']; accent, panel, brand=PALETTE[category]
    is_li = platform == 'linkedin'
    headline=post['image_headline' if is_li else 'facebook_image_headline'].strip()
    sub=post['image_subheading' if is_li else 'facebook_image_subheading'].strip()
    bg='#081321' if category=='technical' else '#171529'
    im=Image.new('RGB',(SIZE,SIZE),bg); d=ImageDraw.Draw(im)
    d.rounded_rectangle((38,38,1042,1042),radius=42,fill=panel,outline=accent,width=3)
    d.rounded_rectangle((82,84,998,92),radius=4,fill=accent)
    d.text((82,125),brand,font=font(21,True),fill='#D9E5F0')
    label='PRACTICAL INSIGHT' if category=='technical' else 'YOUR TAKE?'
    d.rounded_rectangle((82,180,390,234),radius=20,fill='#213650',outline=accent,width=2)
    d.text((101,195),label,font=font(19,True),fill=accent)
    if category=='technical':
        d.rounded_rectangle((800,170,968,308),radius=18,fill='#0A1727',outline='#38536C',width=2)
        for i,c in enumerate(('#FF7B72','#FFC66D','#67D7FF')): d.ellipse((820+i*27,190,836+i*27,206),fill=c)
        for j,w in enumerate((115,92,128,72)): d.rounded_rectangle((820,228+j*18,820+w,235+j*18),radius=3,fill=accent if j==0 else '#536D85')
    else:
        d.rounded_rectangle((810,176,962,290),radius=28,fill='#302B4B',outline=accent,width=3)
        d.polygon([(838,284),(860,284),(841,307)],fill=accent)
        d.text((850,194),'?',font=font(70,True),fill=accent)
    size=70; lines=wrap(d,headline.upper(),830,size,True)
    while len(lines)>4 and size>42: size-=4; lines=wrap(d,headline.upper(),830,size,True)
    if len(lines)>4: size=42; lines=wrap(d,headline.upper(),830,size,True)
    y=355
    for line in lines: d.text((82,y),line,font=font(size,True),fill='#FFFFFF'); y+=size+18
    top=max(700,min(790,y+24))
    d.rounded_rectangle((82,top,998,top+150),radius=26,fill='#0B1728',outline='#3C526A',width=2)
    d.rounded_rectangle((108,top+25,117,top+125),radius=4,fill=accent)
    ss=27; sl=wrap(d,sub,790,ss)
    while len(sl)>3 and ss>20: ss-=2; sl=wrap(d,sub,790,ss)
    sy=top+36
    for line in sl[:3]: d.text((145,sy),line,font=font(ss),fill='#D9E4F0'); sy+=ss+9
    d.line((82,965,998,965),fill='#3C526A',width=2)
    d.text((82,982),'WEB DEVELOPMENT  /  SEO  /  DIGITAL BUSINESS',font=font(17,True),fill='#A7B9CB')
    safe=''.join(c if c.isalnum() else '_' for c in post['title'].lower())[:30].strip('_')
    path=OUT/f"{post['run_date']}_{post['slot']}_{index}_{platform}_{safe}.png"; im.save(path,optimize=True); return str(path)
def main():
    p=Path('generated_posts.json'); posts=json.loads(p.read_text(encoding='utf-8'))
    if len(posts)!=1: raise ValueError('Expected exactly one post concept per scheduled run')
    for i,post in enumerate(posts,1):
        post['image_path']=make(post,'linkedin',i); post['facebook_image_path']=make(post,'facebook',i)
        print('LinkedIn image:',post['image_path']); print('Facebook image:',post['facebook_image_path'])
    p.write_text(json.dumps(posts,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__': main()
