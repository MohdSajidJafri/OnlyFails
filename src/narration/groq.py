from typing import Optional
import config
from src.logger import logger

SYSTEM_PROMPT_CURATOR = """You are an expert social media meme editor who writes viral, punchy captions for fail & unexpected video shorts (like Twitter/X memes).

Task:
Convert the provided Reddit post title into a snappy, engaging 4 to 12 word caption.

Guidelines:
1. WORD COUNT: Exactly 4 to 12 words. Neither too short nor too long.
2. RELEVANCE: Directly resemble and reflect the funny/unexpected action in the video based on the post context.
3. VAGUE TITLES: If the Reddit title is lazy, vague, or not to the point (e.g. 'An interesting title', 'Title', 'WCGW', 'Wait for it', 'Interesting', 'lol', 'Seen today', 'Wait till the end', 'Hold my beer'), generate a relatable, punchy general title suited for funny unexpected fails (e.g. 'Bro really thought he had it 💀', 'That escalated way too quickly 😭', 'Never let them know your next move 😂', 'Bro doubted physics for a sec 😂').
4. STYLE: Casual, modern creator humor (e.g. 'Bro doubted physics for a sec 😂', 'Muscle memory is crazy 💀', 'Confidence was high, execution was not 😭').
5. EMOJIS: Include 1 relevant emoji (😂, 💀, 😭, 🤦‍♂️, etc.) at the end.
6. FORMAT: Return ONLY the caption on a single line. Do not include quotes, prefixes, or explanations."""


def generate_curator_caption(title: str, subreddit: str = "") -> str:
    """
    Use Groq to convert raw Reddit titles into 4-12 word viral, snappy captions.
    If no API key is provided or the call fails, cleanly returns the title.
    """
    api_key = config.GROQ_API_KEY
    if not api_key:
        return _fallback_curator_caption(title)

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
    except ImportError:
        return _fallback_curator_caption(title)

    models_to_try = [
        config.LLM_MODEL,
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant"
    ]
    seen = set()
    deduped_models = []
    for m in models_to_try:
        if m and m not in seen:
            seen.add(m)
            deduped_models.append(m)

    prompt = f"Subreddit: r/{subreddit}\nReddit Title: {title}\nCaption:"
    for m in deduped_models:
        try:
            completion = client.chat.completions.create(
                model=m,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_CURATOR},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=60,
                timeout=15
            )
            raw_caption = completion.choices[0].message.content
            if raw_caption:
                cleaned = raw_caption.strip().strip('"\'')
                for prefix in ["Caption:", "Title:", "CAPTION:", "TITLE:"]:
                    if cleaned.startswith(prefix):
                        cleaned = cleaned[len(prefix):].strip().strip('"\'')
                
                words = cleaned.split()
                if 2 <= len(words) <= 15:
                    logger.info(f"✔ Groq generated viral curator caption: '{cleaned}' ({len(words)} words)")
                    return cleaned
                elif len(words) > 15:
                    cleaned = " ".join(words[:12])
                    return cleaned
        except Exception:
            continue

    return _fallback_curator_caption(title)


def _fallback_curator_caption(title: str) -> str:
    """Safe local fallback for caption generation."""
    clean = title.strip()
    words = clean.split()
    vague_patterns = [
        "an interesting title", "title", "wcgw", "wait for it",
        "wait till the end", "lol", "interesting", "seen today", "hold my beer"
    ]
    if clean.lower().strip(".,!?:") in vague_patterns or len(words) <= 1:
        return "Bro really thought he had it 💀"
    
    if len(words) > 12:
        return " ".join(words[:12]) + " 💀"
    return clean
