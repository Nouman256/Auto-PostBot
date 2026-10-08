import json
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SIZE = 1080
OUT = Path('generated_images')
OUT.mkdir(exist_ok=True)
FONT_DIR = Path('/usr/share/fonts/truetype/dejavu')
PALETTE = {
    'Web Development': ('#A9E8CB', 'WEB DEVELOPMENT', '01'),
    'Search Engine Optimization (SEO)': ('#91C8FF', 'SEO & AI SEARCH', '02'),
    'Digital Marketing': ('#FFC99B', 'DIGITAL MARKETING', '03'),
}

def font(size, bold=False):
    file = 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'
    return ImageFont.truetype(str(FONT_DIR / file), size)

def wrap_to_width(draw, text, max_width, size, bold=False):
    words = text.split()
    lines, current = [], ''
    for word in words:
        candidate = (current + ' ' + word).strip()
        if draw.textbbox((0, 0), candidate, font=font(size, bold))[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def graphic(post, index):
    topic = post.get('topic', 'Web Development')
    accent, category, number = PALETTE.get(topic, PALETTE['Web Development'])
    headline = post.get('image_headline', '').strip()
    sub = post.get('image_subheading', '').strip()
    if not headline or not sub:
        raise ValueError('Missing dynamic image headline or subheading')
    image = Image.new('RGB', (SIZE, SIZE), '#0B1322')
    d = ImageDraw.Draw(image)
    d.rounded_rectangle((45, 45, 1035, 1035), radius=38, fill='#132239', outline='#2C4055', width=2)
    d.rounded_rectangle((95, 105, 180, 113), radius=4, fill=accent)
    d.text((95, 145), 'INSIGHTS  /  DIGITAL GROWTH', font=font(22, True), fill='#CBD8E6')
    d.rounded_rectangle((905, 127, 980, 194), radius=16, fill='#213650')
    d.text((925, 144), number, font=font(30, True), fill=accent)
    d.text((95, 260), category, font=font(26, True), fill=accent)

    size = 74
    while size >= 42:
        lines = wrap_to_width(d, headline.upper(), 860, size, True)
        if len(lines) <= 4:
            break
        size -= 4
    if len(lines) > 4:
        raise ValueError('Image headline does not fit')
    y = 325
    for line in lines:
        d.text((92, y), line, font=font(size, True), fill='#FFFFFF')
        y += size + 22
    if y > 720:
        raise ValueError('Image headline overflows')

    d.rounded_rectangle((95, 748, 985, 902), radius=24, fill='#0C182A', outline='#35506B', width=2)
    d.rounded_rectangle((120, 778, 128, 868), radius=4, fill=accent)
    sub_size = 29
    sub_lines = wrap_to_width(d, sub, 780, sub_size)
    if len(sub_lines) > 3:
        sub_size = 25
        sub_lines = wrap_to_width(d, sub, 780, sub_size)
    if len(sub_lines) > 3:
        raise ValueError('Image subheading too long')
    sy = 778 + max(0, (92 - len(sub_lines) * (sub_size + 9)) // 2)
    for line in sub_lines:
        d.text((151, sy), line, font=font(sub_size), fill='#D9E4F0')
        sy += sub_size + 9
    d.line((95, 950, 985, 950), fill='#36516B', width=2)
    d.text((95, 967), 'WEB  /  SEO  /  MARKETING', font=font(19, True), fill='#A7B9CB')
    path = OUT / f'post_{index:02d}.png'
    image.save(path, optimize=True)
    return str(path)

def main():
    path = Path('generated_posts.json')
    posts = json.loads(path.read_text(encoding='utf-8'))
    for i, post in enumerate(posts, 1):
        post['image_path'] = graphic(post, i)
        print('Generated professional graphic:', post['image_path'])
    path.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
