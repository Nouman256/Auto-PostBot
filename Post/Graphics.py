"""Premium platform-specific PIL artwork; zero extra dependencies."""
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SIZE = 1080
OUT = Path('generated_images')
OUT.mkdir(exist_ok=True)
FONT_DIR = Path('/usr/share/fonts/truetype/dejavu')
ACCENTS = {
    'Web Development': ('#64E4C1', 'WEB DEVELOPMENT', 'web'),
    'Search Engine Optimization (SEO)': ('#8CABFF', 'SEO / SEARCH', 'seo'),
    'Digital Marketing': ('#FFC080', 'DIGITAL MARKETING', 'marketing'),
}

def font(size, bold=False):
    name = 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'
    return ImageFont.truetype(str(FONT_DIR / name), size)

def rgb(value):
    return tuple(bytes.fromhex(value.lstrip('#')))

def text_lines(draw, string, limit, size, bold=False, max_lines=None):
    f = font(size, bold)
    lines, current = [], ''
    for word in string.split():
        candidate = f'{current} {word}'.strip()
        if draw.textbbox((0, 0), candidate, font=f)[2] <= limit:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    if max_lines and len(lines) > max_lines:
        return None
    return lines

def draw_wrapped(draw, string, x, y, width, size, fill, bold=False, max_lines=3, step=None):
    while size >= 19:
        lines = text_lines(draw, string, width, size, bold, max_lines)
        if lines is not None:
            break
        size -= 2
    if lines is None:
        raise ValueError('Text too long for graphic; shorten generated image copy')
    for line in lines:
        draw.text((x, y), line, font=font(size, bold), fill=fill)
        y += step or (size + 15)
    return y

def base(accent, platform):
    im = Image.new('RGB', (SIZE, SIZE))
    p = im.load()
    for y in range(SIZE):
        a = y / SIZE
        for x in range(SIZE):
            glow = max(0, 1 - math.hypot(x-900, y-120)/900) * .11
            p[x, y] = (int(11 + a*6 + glow*45), int(20+a*9+glow*65), int(37+a*12+glow*65))
    d = ImageDraw.Draw(im)
    d.ellipse((790, -230, 1260, 240), outline='#284457', width=3)
    d.ellipse((840, -180, 1210, 190), outline='#254052', width=2)
    d.rounded_rectangle((48, 48, 1032, 1032), radius=32, outline='#294356', width=2)
    d.rounded_rectangle((82, 81, 135, 134), radius=14, fill=accent)
    d.text((96, 90), 'T', fill='#0D1D2A', font=font(30, True))
    d.text((152, 91), 'TECHVISION', fill='#F3F8FE', font=font(30, True))
    d.text((155, 126), 'PRACTICAL DIGITAL INSIGHTS', fill='#A0B4C7', font=font(15, True))
    d.line((83, 165, 996, 165), fill='#2A4556', width=2)
    return im, d

def draw_visual(draw, kind, accent, x, y, width, height, platform):
    """Recognizable vector-style dashboard with subject-specific illustration."""
    draw.rounded_rectangle((x, y, x+width, y+height), radius=30, fill='#152B3D', outline='#426070', width=2)
    draw.rounded_rectangle((x+22, y+20, x+width-22, y+55), radius=10, fill='#243D4D')
    for j,c in enumerate(('#FF8E8E','#FFD28C','#80DBBB')):
        draw.ellipse((x+38+j*24,y+32,x+49+j*24,y+43),fill=c)
    if kind=='web':
        draw.rounded_rectangle((x+34,y+83,x+width-34,y+height-28),radius=15,fill='#0D1D2B')
        for k,w in enumerate((155,115,180,95)):
            draw.rounded_rectangle((x+59,y+113+k*38,x+59+w,y+122+k*38),radius=5, fill=accent if k==0 else '#456C79')
        draw.rounded_rectangle((x+width-192,y+98,x+width-53,y+height-49),radius=13,fill='#245465')
        draw.ellipse((x+width-158,y+125,x+width-90,y+193),outline=accent,width=8)
        draw.rounded_rectangle((x+width-168,y+214,x+width-75,y+226),radius=5,fill='#D2E6ED')
    elif kind=='seo':
        draw.rounded_rectangle((x+35,y+87,x+width-35,y+142),radius=23,outline='#6C9CAD',width=3)
        draw.ellipse((x+58,y+103,x+80,y+125),outline=accent,width=4)
        draw.line((x+77,y+122,x+91,y+136),fill=accent,width=4)
        for k,l in enumerate((.90,.72,.82)):
            yy=y+167+k*55
            draw.rounded_rectangle((x+45,yy,x+width-45,yy+43),radius=12,fill='#20394A')
            draw.rounded_rectangle((x+62,yy+13,x+62+int((width-140)*l),yy+21),radius=4,fill=accent if k==0 else '#6C8496')
    else:
        labels=['REACH','ENGAGE','CONVERT']
        for k in range(3):
            xx=x+38+k*(width-76)//3
            bar_h=(84,145,110)[k]
            draw.rounded_rectangle((xx,y+height-52-bar_h,xx+(width-110)//3,y+height-52),radius=13,fill=accent if k==1 else '#446B78')
            draw.text((xx,y+height-39),labels[k],font=font(14,True),fill='#D2E8EF')
        draw.line((x+58,y+134,x+165,y+101,x+277,y+131,x+width-60,y+88),fill='#E7F3FF',width=6,joint='curve')

def graphic(post, index, platform='linkedin'):
    topic=post.get('topic','Web Development')
    accent,category,kind=ACCENTS.get(topic,ACCENTS['Web Development'])
    if platform=='facebook':
        headline=(post.get('facebook_image_headline') or post.get('image_headline') or '').strip()
        sub=(post.get('facebook_image_subheading') or post.get('image_subheading') or '').strip()
        points=post.get('facebook_visual_points') or []
    else:
        headline=(post.get('image_headline') or '').strip()
        sub=(post.get('image_subheading') or '').strip()
        points=post.get('linkedin_visual_points') or []
    if not headline or not sub:
        raise ValueError('Missing dynamic image headline/subheading')
    if not isinstance(points,list) or len(points)!=3 or any(not isinstance(v,str) or not v.strip() for v in points):
        # Keep backward compatibility with older generation JSON.
        points=['Identify the bottleneck','Choose a focused fix','Measure the result']
    im,d=base(accent,platform)
    d.rounded_rectangle((83, 200, 354, 247), radius=23, fill='#213B4B')
    d.ellipse((102,216,116,230),fill=accent)
    d.text((127,211),category,font=font(18,True),fill='#EEF6FC')
    d.text((84,279),'THE BETTER WAY TO',font=font(20,True),fill=accent)
    draw_wrapped(d,headline.upper(),81,324,915,61,'#FFFFFF',True,3,79)
    draw_wrapped(d,sub,84,575,905,25,'#C3D5E4',False,2,37)
    # The lower section provides actual visual hierarchy, not another empty dark box.
    draw_visual(d,kind,accent,82,687,460,263,platform)
    for j,point in enumerate(points):
        cy=694+j*83
        d.rounded_rectangle((567,cy,996,cy+70),radius=16,fill='#203749' if platform=='linkedin' else '#243B4A')
        d.rounded_rectangle((584,cy+16,622,cy+54),radius=11,fill=accent)
        d.text((594,cy+22),str(j+1),fill='#09202D',font=font(19,True))
        draw_wrapped(d,point,637,cy+17,341,20,'#EDF5FC',True,2,27)
    d.line((83,978,996,978),fill='#385361',width=2)
    d.text((84,989),'TECHVISION  /  DIGITAL EDUCATION',font=font(17,True),fill='#9FB9C9')
    d.text((875,989),platform.upper(),font=font(16,True),fill=accent)
    name=f'post_{index:02d}.png' if platform=='linkedin' else f'post_{index:02d}_facebook.png'
    dest=OUT/name
    im.save(dest,optimize=True)
    return str(dest)

def main():
    path=Path('generated_posts.json')
    posts=json.loads(path.read_text(encoding='utf-8'))
    for i,post in enumerate(posts,1):
        post['image_path']=graphic(post,i,'linkedin')
        if post.get('facebook_content'):
            post['facebook_image_path']=graphic(post,i,'facebook')
        print('Generated LinkedIn / Facebook graphics:',post['image_path'],post.get('facebook_image_path'))
    path.write_text(json.dumps(posts,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':
    main()
