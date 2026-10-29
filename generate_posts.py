import json, os, re, hashlib
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

API_KEY = os.getenv('GEMINI_API_KEY', '').strip()
MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash').strip()
POST_FILE = Path('generated_posts.json')
HISTORY_FILE = Path('post_history.json')
TZ = ZoneInfo('Asia/Karachi')

SLOT = os.getenv('POST_SLOT', '').strip().lower()
if SLOT not in {'noon', 'evening'}:
    now = datetime.now(TZ)
    SLOT = 'noon' if now.hour < 14 else 'evening'

PROMPTS = {
 'noon': '''Create ONE genuinely useful, specific, original educational social post for a digital agency founder. Topics may include SEO, guest posting, link building, WordPress, web development, site speed, technical SEO, content strategy, analytics, or digital business. It should teach a practical idea with a clear takeaway, not sound like generic AI advice. Include a strong opening, readable short paragraphs, useful bullets only where appropriate, a natural discussion question, and 3-5 relevant hashtags. Do not invent statistics, case studies, personal experience, guarantees, or sources. Brand signature: — Muhammad Nouman | Founder & Team Head, TechVision Digital. Return distinct LinkedIn and Facebook versions: LinkedIn can be more professional and detailed; Facebook should be more conversational and concise. Each platform needs its own image headline and subheading, not just a copy of the other.''',
 'evening': '''Create ONE engaging social post for a digital agency founder. It should invite genuine comments through an interesting dilemma, relatable digital-work situation, thoughtful question, mini-poll, or occasional light professional humor. Rotate formats and avoid repeating common generic prompts. Topics may include SEO, guest posting, clients, WordPress, web development, agency life, freelancing, digital business, or online work. Make it interesting without rage bait, fake stories, or fabricated personal experience. Include a clear question people can answer, 3-5 relevant hashtags, and signature: — Muhammad Nouman | Founder & Team Head, TechVision Digital. Return distinct LinkedIn and Facebook versions: LinkedIn professional and discussion-led; Facebook warmer, shorter, and more casual. Each platform needs its own image headline and subheading.'''
}

def recent_topics():
    if not HISTORY_FILE.exists(): return []
    try: data = json.loads(HISTORY_FILE.read_text(encoding='utf-8'))
    except (ValueError, OSError): return []
    return [f"{x.get('title','')} — {x.get('topic','')}" for x in data[-40:] if isinstance(x, dict)]

def extract_json(text):
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text, flags=re.I)
    start, end = text.find('{'), text.rfind('}')
    if start < 0 or end < start: raise ValueError('Gemini response did not contain a JSON object')
    return json.loads(text[start:end+1])

def main():
    if not API_KEY: raise RuntimeError('GEMINI_API_KEY is missing')
    history = recent_topics()
    prompt = PROMPTS[SLOT] + '\n\nAvoid duplicating these recent topics/titles: ' + json.dumps(history, ensure_ascii=False)
    prompt += '''\nReturn ONLY valid JSON with this exact shape: {"title":"...","topic":"...","category":"technical or engagement","linkedin_content":"...","facebook_content":"...","image_headline":"...","image_subheading":"...","facebook_image_headline":"...","facebook_image_subheading":"..."}. Keep all four image text fields concise and readable. category must be technical for noon and engagement for evening.'''
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent'
    response = requests.post(url, params={'key': API_KEY}, json={
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {'temperature': 0.9, 'responseMimeType': 'application/json'}
    }, timeout=90)
    if not response.ok: raise RuntimeError(f'Gemini API failed: HTTP {response.status_code}: {response.text[:500]}')
    body = response.json()
    try: text = body['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError, TypeError): raise RuntimeError(f'Unexpected Gemini response: {json.dumps(body)[:500]}')
    post = extract_json(text)
    required = ['title','topic','category','linkedin_content','facebook_content','image_headline','image_subheading','facebook_image_headline','facebook_image_subheading']
    for key in required:
        if not isinstance(post.get(key), str) or not post[key].strip(): raise ValueError(f'Generated post missing required field: {key}')
    post['category'] = 'technical' if SLOT == 'noon' else 'engagement'
    post['run_date'] = datetime.now(TZ).strftime('%Y-%m-%d')
    post['slot'] = SLOT
    post['dedupe_key'] = hashlib.sha256(f"{post['run_date']}|{SLOT}|{post['title']}".encode()).hexdigest()[:20]
    post['content'] = post['linkedin_content']
    post['facebook_content'] = post['facebook_content']
    POST_FILE.write_text(json.dumps([post], ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Generated {SLOT} post: {post['title']} ({post['category']})")
    print('\nLINKEDIN PREVIEW\n' + post['linkedin_content'])
    print('\nFACEBOOK PREVIEW\n' + post['facebook_content'])

if __name__ == '__main__': main()
