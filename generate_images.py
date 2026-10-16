import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SIZE = 1080
OUT = Path("generated_images")
OUT.mkdir(exist_ok=True)
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
if not FONT_DIR.exists():
    FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")

PALETTE = {
    "technical": ("#67D7FF", "#132239", "TECHVISION / TECH INSIGHTS"),
    "engagement": ("#FFC66D", "#24203A", "TECHVISION / COMMUNITY"),
}

def font(size, bold=False):
    filename = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(str(FONT_DIR / filename), size)

def wrap_to_width(draw, text, max_width, size, bold=False):
    words = text.split()
    lines, current = [], ""
    fnt = font(size, bold)
    for word in words:
        candidate = (current + " " + word).strip()
        if draw.textbbox((0, 0), candidate, font=fnt)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def draw_chip(draw, x, y, label, accent):
    draw.rounded_rectangle((x, y, x + 300, y + 54), radius=20, fill="#213650", outline=accent, width=2)
    draw.text((x + 18, y + 13), label.upper()[:24], font=font(19, True), fill=accent)

def make_graphic(post, index, platform):
    category = post["category"]
    accent, secondary, brandline = PALETTE[category]
    if platform == "linkedin":
        headline = post["image_headline"].strip()
        sub = post["image_subheading"].strip()
    else:
        headline = post["facebook_image_headline"].strip()
        sub = post["facebook_image_subheading"].strip()

    # Category-specific compositions: technical = structured dashboard; engagement = bold meme/question card.
    bg = "#081321" if category == "technical" else "#171529"
    image = Image.new("RGB", (SIZE, SIZE), bg)
    d = ImageDraw.Draw(image)
    d.rounded_rectangle((38, 38, 1042, 1042), radius=42, fill=secondary, outline=accent, width=3)
    d.rounded_rectangle((82, 84, 998, 92), radius=4, fill=accent)
    d.text((82, 125), brandline, font=font(21, True), fill="#D9E5F0")
    draw_chip(d, 82, 180, "TECHNICAL TIP" if category == "technical" else "COMMUNITY POST", accent)

    # Decorative, category-specific motif; no external/copyrighted imagery.
    if category == "technical":
        # Browser / code-panel motif.
        d.rounded_rectangle((790, 175, 965, 315), radius=18, fill="#0A1727", outline="#38536C", width=2)
        for i, c in enumerate(("#FF7B72", "#FFC66D", "#67D7FF")):
            d.ellipse((810 + i * 27, 195, 826 + i * 27, 211), fill=c)
        for j, w in enumerate((115, 92, 128, 72)):
            d.rounded_rectangle((810, 232 + j * 18, 810 + w, 239 + j * 18), radius=3, fill=accent if j == 0 else "#536D85")
    else:
        # Speech bubble and sparkle motif for questions/memes.
        d.rounded_rectangle((795, 180, 962, 300), radius=28, fill="#302B4B", outline=accent, width=3)
        d.polygon([(830, 294), (850, 294), (833, 320)], fill=accent)
        d.text((836, 205), "?", font=font(74, True), fill=accent)
        d.ellipse((930, 320, 954, 344), fill=accent)
        d.ellipse((780, 325, 795, 340), fill="#FFFFFF")

    size = 72
    lines = wrap_to_width(d, headline.upper(), 820, size, True)
    while len(lines) > 4 and size > 42:
        size -= 4
        lines = wrap_to_width(d, headline.upper(), 820, size, True)
    if len(lines) > 4:
        raise ValueError(f"Headline does not fit: {headline}")
    y = 360
    for line in lines:
        d.text((82, y), line, font=font(size, True), fill="#FFFFFF")
        y += size + 20

    box_top = max(720, min(790, y + 30))
    d.rounded_rectangle((82, box_top, 998, box_top + 145), radius=26, fill="#0B1728", outline="#3C526A", width=2)
    d.rounded_rectangle((108, box_top + 25, 117, box_top + 120), radius=4, fill=accent)
    sub_size = 28
    sub_lines = wrap_to_width(d, sub, 790, sub_size, False)
    if len(sub_lines) > 3:
        sub_size = 23
        sub_lines = wrap_to_width(d, sub, 790, sub_size, False)
    if len(sub_lines) > 3:
        raise ValueError(f"Subheading too long: {sub}")
    sy = box_top + 37
    for line in sub_lines:
        d.text((145, sy), line, font=font(sub_size), fill="#D9E4F0")
        sy += sub_size + 9

    d.line((82, 965, 998, 965), fill="#3C526A", width=2)
    d.text((82, 982), "WEB DEVELOPMENT  /  SEO  /  DIGITAL BUSINESS", font=font(17, True), fill="#A7B9CB")
    safe_title = "".join(c if c.isalnum() else "_" for c in post["title"].lower())[:30].strip("_")
    path = OUT / f"{post['run_date']}_{index:02d}_{category}_{platform}_{safe_title}.png"
    image.save(path, optimize=True)
    return str(path)

def main():
    path = Path("generated_posts.json")
    posts = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(posts, list) or len(posts) != 2:
        raise ValueError("Expected exactly two posts: technical and engagement")
    for index, post in enumerate(posts, 1):
        post["image_path"] = make_graphic(post, index, "linkedin")
        post["facebook_image_path"] = make_graphic(post, index, "facebook")
        print(f"Images created for {post['category']}: {post['image_path']} / {post['facebook_image_path']}")
    path.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
