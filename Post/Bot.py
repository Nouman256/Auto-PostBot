prompt = f"""You are an elite B2B Tech & SEO Content Strategist. Create TWO DISTINCT professional social media posts about {topic}.
Today: {today}. Avoid repeating these recent angles: {json.dumps(recent_topics[-25:])}.

CRITICAL WRITING RULES (SEO & Professional Standards):
- NEVER write heavy unformatted blocks of text or boring paragraphs.
- Use a strong attention-grabbing hook at the beginning.
- Break down technical concepts into clean, scannable bullet points (using ✓, →, or •).
- Maintain an authoritative yet approachable expert tone.
- Add relevant high-value hashtags at the end.

LINKEDIN (JSON key 'content'):
- 120-180 words. Professional B2B style, focused on deep technical value, architecture, or optimization strategy.

FACEBOOK (JSON key 'facebook_content'):
- 80-130 words. Slightly more conversational, community-driven, actionable quick tip or checklist format (Distinct from LinkedIn).

AI IMAGE GENERATION PROMPT (JSON key 'ai_image_prompt'):
- Create a detailed, highly professional visual prompt for an AI image generator (e.g., modern web development workspace, clean minimalist UI design, professional SEO analytics dashboard on a sleek laptop, cinematic lighting, 4k). NO text inside the image prompt.

Return ONLY valid JSON with string keys:
"title", "content", "facebook_content", "ai_image_prompt".
"""
