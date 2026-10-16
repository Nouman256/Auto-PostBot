import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path('generated_images')
OUT.mkdir(exist_ok=True)

def get_font(size):
    # System fonts fallback try karna taake server par error na aaye
    for font_name in ["arial.ttf", "DejaVuSans-Bold.ttf", "Arial.ttf"]:
        try:
            return ImageFont.truetype(font_name, size)
        except IOError:
            continue
    return ImageFont.load_default()

def create_professional_graphic(post, index, platform='linkedin'):
    # Dimensions for modern social media (1200x630 pixels)
    width, height = 1200, 630
    img = Image.new("RGB", (width, height), color="#0F172A") # Dark slate premium background
    draw = ImageDraw.Draw(img)

    # Decorative top accent bar (Gradient/Solid brand color)
    draw.rectangle([(0, 0), (width, 12)], fill="#3B82F6") # Modern Blue accent

    # Branding / Watermark text top-left
    font_brand = get_font(22)
    draw.text((60, 50), "TECHVISION DIGITAL", fill="#60A5FA", font=font_brand)

    # Category / Badge top-right
    slot = post.get('slot', 'TECHNICAL INSIGHT').upper()
    font_badge = get_font(20)
    draw.text((width - 300, 50), f"// {slot}", fill="#94A3B8", font=font_badge)

    # Main Title (The core hook of the post)
    title = post.get('title', 'WordPress & SEO Expert Strategy')
    font_title = get_font(42)
    
    # Text wrapping for title
    margin = 60
    max_width = width - 120
    
    # Word wrap logic
    words = title.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + " " + word if current_line else word
        bbox = font_title.getbbox(test_line)
        if (bbox[2] - bbox[0]) <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    # Draw title lines
    y_text = 130
    for line in lines[:3]: # Max 3 lines
        draw.text((margin, y_text), line, fill="#F8FAFC", font=font_title)
        y_text += 60

    # Divider line
    y_text += 20
    draw.line([(margin, y_text), (width - margin, y_text)], fill="#334155", width=2)
    y_text += 40

    # Key bullet points or takeaway box extracted from content
    font_body = get_font(26)
    content_text = post.get('content', '')
    # Extracting first sentence or bullet as a key highlight
    highlights = [line.strip() for line in content_text.split('\n') if line.strip().startswith(('✓', '-', '•'))]
    if not highlights:
        highlights = ["✓ Enterprise Architecture & Core Web Vitals", "✓ Scalable Performance Optimization"]

    for highlight in highlights[:3]:
        draw.text((margin, y_text), highlight[:75], fill="#E2E8F0", font=font_body)
        y_text += 45

    # Footer Website / Tagline
    font_footer = get_font(20)
    draw.text((margin, height - 60), "www.techvisiondigital.com | Expert Insights", fill="#64748B", font=font_footer)

    # Save file
    suffix = "" if platform == 'linkedin' else "_facebook"
    filename = f"post_{index:02d}{suffix}.png"
    file_path = OUT / filename
    img.save(file_path, "PNG", quality=95)
    print(f"Professional graphic generated at: {file_path}")
    return str(file_path)

def main():
    path = Path('generated_posts.json')
    if not path.exists():
        print("generated_posts.json not found!")
        return
        
    posts = json.loads(path.read_text(encoding='utf-8'))
    for i, post in enumerate(posts, 1):
        post['image_path'] = create_professional_graphic(post, i, 'linkedin')
        if post.get('facebook_content'):
            post['facebook_image_path'] = create_professional_graphic(post, i, 'facebook')
            
    path.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Professional branded graphics generation completed.")

if __name__ == '__main__':
    main()
