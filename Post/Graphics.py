import json
from pathlib import Path
import requests

OUT = Path('generated_images')
OUT.mkdir(exist_ok=True)

def generate_pollinations_ai_image(prompt, output_filename):
    """Pollinations.ai se high-quality, sharp aur professional AI image generate karna"""
    try:
        # High quality parameters aur sharp focus ke sath prompt enhance karna
        enhanced_prompt = f"{prompt}, professional commercial photography, ultra-detailed, 8k resolution, photorealistic, sharp focus, perfect studio lighting, corporate tech aesthetic"
        
        encoded_prompt = requests.utils.quote(enhanced_prompt)
        # width aur height specify karna taake image high resolution aur standard social media size mein bane
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&nologo=true&enhance=true"
        
        print(f"Generating High-Quality AI Image: {enhanced_prompt}")
        response = requests.get(image_url, timeout=60)
        
        if response.status_code == 200:
            file_path = OUT / output_filename
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"AI Image saved successfully at: {file_path}")
            return str(file_path)
        else:
            print(f"Pollinations API returned status code {response.status_code}")
    except Exception as e:
        print(f"Error generating AI image: {e}")
    return None

def main():
    path = Path('generated_posts.json')
    if not path.exists():
        print("generated_posts.json not found!")
        return
        
    posts = json.loads(path.read_text(encoding='utf-8'))
    for i, post in enumerate(posts, 1):
        # LinkedIn ke liye alag prompt
        linkedin_prompt = post.get('ai_image_prompt') or "Professional web development dashboard and code architecture on sleek laptop screen"
        linkedin_filename = f"post_{i:02d}.png"
        post['image_path'] = generate_pollinations_ai_image(linkedin_prompt, linkedin_filename)
        
        # Facebook ke liye alag prompt (agar na ho toh fallback LinkedIn wala ya unique ho)
        fb_prompt = post.get('facebook_ai_image_prompt') or post.get('ai_image_prompt') or "Modern developer workspace with clean aesthetic"
        fb_filename = f"post_{i:02d}_facebook.png"
        post['facebook_image_path'] = generate_pollinations_ai_image(fb_prompt, fb_filename)
            
    path.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Graphics generation completed with distinct, high-quality platform images.")

if __name__ == '__main__':
    main()
