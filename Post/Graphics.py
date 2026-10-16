import json
import math
from pathlib import Path
import requests
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

def generate_pollinations_ai_image(prompt, output_filename):
    """Free AI image generation using Pollinations.ai"""
    try:
        encoded_prompt = requests.utils.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        response = requests.get(image_url, timeout=30)
        if response.status_code == 200:
            file_path = OUT / output_filename
            with open(file_path, "wb") as f:
                f.write(response.content)
            return str(file_path)
    except Exception as e:
        print(f"AI Image generation failed: {e}, falling back to default graphic.")
    return None

def graphic(post, index, platform='linkedin'):
    slot = post.get('slot', 'technical')
    
    # Agar post entertainment/meme ki hai toh Free AI Image (Pollinations.ai) use karein
    if slot == 'entertainment' and post.get('ai_image_prompt'):
        ai_prompt = post.get('ai_image_prompt')
        suffix = "" if platform == 'linkedin' else "_facebook"
        filename = f"post_{index:02d}{suffix}_ai.png"
        ai_img_path = generate_pollinations_ai_image(ai_prompt, filename)
        if ai_img_path:
            return ai_img_path

    # Standard Technical Infographic Logic (PIL)
    topic = post.get('topic', 'Web Development')
    accent, category, kind = ACCENTS.get(topic, ACCENTS['Web Development'])
    
    im = Image.new('RGB', (SIZE, SIZE), color='#0D1D2A')
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((48, 48, 1032, 1032), radius=32, outline='#294356', width=2)
    d.text((96, 90), 'TECHVISION', fill='#F3F8FE', font=font(30, True))
    
    name = f'post_{index:02d}.png' if platform == 'linkedin' else f'post_{index:02d}_facebook.png'
    dest = OUT / name
    im.save(dest, optimize=True)
    return str(dest)

def main():
    path = Path('generated_posts.json')
    posts = json.loads(path.read_text(encoding='utf-8'))
    for i, post in enumerate(posts, 1):
        post['image_path'] = graphic(post, i, 'linkedin')
        if post.get('facebook_content'):
            post['facebook_image_path'] = graphic(post, i, 'facebook')
    path.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == '__main__':
    main()
