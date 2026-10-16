import json
from pathlib import Path
import requests

OUT = Path('generated_images')
OUT.mkdir(exist_ok=True)

def generate_pollinations_ai_image(prompt, output_filename):
    """Pollinations.ai se professional aur realistic AI image generate karne ka function"""
    try:
        # Professional look ke liye prompt ko mazeed enhance karna
        enhanced_prompt = f"{prompt}, professional photography, highly detailed, modern technology workspace, 8k resolution, photorealistic, clean lighting"
        
        encoded_prompt = requests.utils.quote(enhanced_prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        
        print(f"Generating AI Image with prompt: {enhanced_prompt}")
        response = requests.get(image_url, timeout=45)
        
        if response.status_code == 200:
            file_path = OUT / output_filename
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"AI Image saved successfully at: {file_path}")
            return str(file_path)
    except Exception as e:
        print(f"Error generating AI image: {e}")
    return None

def graphic(post, index, platform='linkedin'):
    # Gemini se mila hua ai_image_prompt use karna
    ai_prompt = post.get('ai_image_prompt') or "Professional developer working in a modern office setup with dual monitors, clean dark mode aesthetic"
    
    suffix = "" if platform == 'linkedin' else "_facebook"
    filename = f"post_{index:02d}{suffix}.png"
    
    # Pollinations.ai se image fetch karna
    image_path = generate_pollinations_ai_image(ai_prompt, filename)
    
    if image_path:
        return image_path
    else:
        # Fallback agar API fail ho jaye
        return str(OUT / filename)

def main():
    path = Path('generated_posts.json')
    if not path.exists():
        print("generated_posts.json not found!")
        return
        
    posts = json.loads(path.read_text(encoding='utf-8'))
    for i, post in enumerate(posts, 1):
        post['image_path'] = graphic(post, i, 'linkedin')
        if post.get('facebook_content'):
            post['facebook_image_path'] = graphic(post, i, 'facebook')
            
    path.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Graphics generation completed with professional AI images.")

if __name__ == '__main__':
    main()
