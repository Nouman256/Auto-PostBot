
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SIZE = 1080
BG = "#0B1220"
CARD = "#142238"
LIME = "#BFF747"
WHITE = "#FFFFFF"
GRAY = "#B8C6D5"

OUTPUT = Path("generated_images")
OUTPUT.mkdir(exist_ok=True)

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")

def get_font(size, bold=False):
    filename = (
        "DejaVuSans-Bold.ttf"
        if bold else "DejaVuSans.ttf"
    )
    return ImageFont.truetype(
        str(FONT_DIR / filename), size
    )

DESIGNS = {
    "Web Development": {
        "heading": ["BUILD BETTER", "WEBSITES"],
        "label": "WEB DEVELOPMENT",
        "description": "Design • Performance • Experience",
        "symbol": "</>",
        "accent": "#BFF747"
    },
    "Search Engine Optimization (SEO)": {
        "heading": ["GET FOUND", "ON GOOGLE"],
        "label": "SEARCH ENGINE OPTIMIZATION",
        "description": "Content • Technical SEO • Visibility",
        "symbol": "SEO",
        "accent": "#63E6BE"
    },
    "Digital Marketing": {
        "heading": ["GROW YOUR", "DIGITAL REACH"],
        "label": "DIGITAL MARKETING",
        "description": "Strategy • Content • Engagement",
        "symbol": "%",
        "accent": "#F6C177"
    }
}

def make_image(topic, number):
    info = DESIGNS.get(topic, {
        "heading": ["DIGITAL", "GROWTH"],
        "label": "DIGITAL STRATEGY",
        "description": "Learn • Build • Grow",
        "symbol": "+",
        "accent": LIME
    })

    accent = info["accent"]

    img = Image.new("RGB", (SIZE, SIZE), BG)
    draw = ImageDraw.Draw(img)

    # Decorative background
    for radius in range(260, 80, -40):
        draw.ellipse(
            (820-radius, 210-radius,
             820+radius, 210+radius),
            outline="#263D4B",
            width=3
        )

    # Main panel
    draw.rounded_rectangle(
        (55, 55, 1025, 1025),
        radius=45,
        fill=CARD
    )

    # Top accent
    draw.rounded_rectangle(
        (100, 105, 270, 115),
        radius=5,
        fill=accent
    )

    draw.text(
        (100, 155),
        "DIGITAL GROWTH SERIES",
        font=get_font(26, True),
        fill=accent
    )

    # Number
    draw.rounded_rectangle(
        (860, 145, 970, 225),
        radius=22,
        fill=BG
    )

    draw.text(
        (884, 162),
        f"{number:02d}",
        font=get_font(37, True),
        fill=accent
    )

    # Topic label
    draw.text(
        (100, 315),
        info["label"],
        font=get_font(24, True),
        fill=accent
    )

    # Headline
    y = 390
    for line in info["heading"]:
        draw.text(
            (95, y),
            line,
            font=get_font(66, True),
            fill=WHITE
        )
        y += 100

    # Description
    draw.text(
        (100, 640),
        info["description"],
        font=get_font(25),
        fill=GRAY
    )

    # Visual section
    draw.rounded_rectangle(
        (100, 735, 980, 890),
        radius=28,
        fill=BG,
        outline="#315062",
        width=3
    )

    draw.text(
        (145, 775),
        info["symbol"],
        font=get_font(57, True),
        fill=accent
    )

    draw.text(
        (420, 795),
        "LEARN  •  APPLY  •  GROW",
        font=get_font(23, True),
        fill=WHITE
    )

    # Footer
    draw.line(
        (100, 940, 980, 940),
        fill="#315062",
        width=2
    )

    draw.text(
        (100, 965),
        "WEB  /  SEO  /  MARKETING",
        font=get_font(20, True),
        fill=GRAY
    )

    filename = OUTPUT / f"post_{number:02d}.png"
    img.save(filename, optimize=True)

    print(f"Created: {filename}")
    return str(filename)


def main():
    with open(
        "generated_posts.json",
        "r",
        encoding="utf-8"
    ) as file:
        posts = json.load(file)

    for number, post in enumerate(posts, 1):
        image_path = make_image(
            post["topic"],
            number
        )
        post["image_path"] = image_path

    with open(
        "generated_posts.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            posts,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("All graphics generated successfully!")


if __name__ == "__main__":
    main()
