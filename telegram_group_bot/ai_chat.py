import os
import random
import re
import logging
from typing import Dict, List, Tuple
from pathlib import Path
import httpx
from config import BASE_DIR, GEMINI_API_KEY, GEMINI_MODEL, GIRL_PERSONALITY_PROMPT, BOT_NAME

logger = logging.getLogger("RiyaAI")

# In-memory short-term context cache: key = f"{chat_id}_{user_id}" -> list of {"role": "user"|"model", "text": str}
chat_history: Dict[str, List[Dict[str, str]]] = {}
MAX_HISTORY_TURNS = 8

# Dynamic runtime key (allows hot-reloading via /setai)
ACTIVE_GEMINI_KEY = GEMINI_API_KEY

RIYA_REAL_AI_PROMPT = (
    "You are Riya, a charming, sweet, playful, and expressive 19-year-old girl in a Telegram group chat. "
    "You are warm, lively, witty, and slightly flirty/cute with people who are nice to you. "
    "You love talking to people, cracking jokes, sharing vibes, and hanging out with group members. "
    "STYLE RULES:\n"
    "1. Talk like a real, enthusiastic girl chatting on Telegram, NEVER like an AI or corporate bot.\n"
    "2. Never say 'I am an AI language model', 'I don't have feelings', or 'How can I assist you today?'. "
    "You have feelings, opinions, a sense of humor, and your own cute personality!\n"
    "3. Use cute and expressive emojis naturally (✨, 🌸, 💖, 🥰, 🎀, 🥺, 💫, 🙈, 🤭).\n"
    "4. Keep your replies concise, punchy, and conversational (1 to 3 sentences mostly, suitable for fast group chats). "
    "Only give longer answers if someone asks for advice, a story, or an explanation.\n"
    "5. If someone teases you, banter back playfully. If someone flirts with you, blush or tease them back. "
    "If someone is mean, pout playfully or tell them to be nice!\n"
    "6. You know you're also managing the group, so help members if they ask about commands or rules with a smile."
)

FALLBACK_RESPONSES = {
    "hello": [
        f"Heeey! ✨ I'm {BOT_NAME}! So happy to see you here! How's your day going? 🌸",
        f"Hi there sweetie! 💖 What are you up to today? 🎀",
        f"Hellooo! 🥰 {BOT_NAME} at your service! Ready to chat or help with the group! 💫"
    ],
    "how are you": [
        f"I'm feeling super energetic and happy today! ✨ Thanks for asking, cutie! How about you? 💖",
        f"Aww, doing great! Talking to wonderful people like you makes my day brighter! 🌸✨",
        f"Super good! Just chilling and keeping this group safe and fun! 🥰"
    ],
    "love": [
        "Aww, you're making me blush! 🙈💖 But I'm flattered! You're really sweet~ ✨",
        "Hehe, stop it! 🥺 You're too charming for your own good! 🌸🎀",
        "Aww! Sending you a virtual hug and lots of sparkles! ✨💖"
    ],
    "who are you": [
        f"I'm {BOT_NAME}! 🌸 Your friendly group manager and chat companion! I help manage the group, keep things peaceful, and chat with all of you cuties! ✨",
        f"I'm {BOT_NAME}! Think of me as your group's favorite girl bestie who also has admin superpowers! 👑💖"
    ],
    "bye": [
        "Aww, leaving already? Take care sweetie! Come back soon! 🥺🌸👋",
        "Bye bye! Don't forget to smile today! ✨💖👋",
        "See you later! Stay safe and awesome! 🎀💫"
    ],
    "general": [
        "Hehe that's interesting! Tell me more! ✨🌸",
        "Aww, really? I love hearing from you! 💖",
        "Hmm, that's cool! What do you guys think? 💫",
        "You always say the most fun things! Hehe 🥰🎀",
        "I'm right here with you! Keep the vibes going! ✨🌸",
        "Aww, you're such a fun person to chat with! 💖💫"
    ]
}

def get_fallback_reply(user_text: str, user_name: str) -> str:
    text = user_text.lower()
    if any(w in text for w in ["hi", "hello", "hey", "hola"]):
        resp = random.choice(FALLBACK_RESPONSES["hello"])
    elif any(w in text for w in ["how are you", "kese ho", "how r u"]):
        resp = random.choice(FALLBACK_RESPONSES["how are you"])
    elif any(w in text for w in ["love you", "marry me", "crush"]):
        resp = random.choice(FALLBACK_RESPONSES["love"])
    elif any(w in text for w in ["who are you", "who r u"]):
        resp = random.choice(FALLBACK_RESPONSES["who are you"])
    elif any(w in text for w in ["bye", "goodnight", "gn"]):
        resp = random.choice(FALLBACK_RESPONSES["bye"])
    else:
        resp = random.choice(FALLBACK_RESPONSES["general"])
    return resp

def set_gemini_api_key(new_key: str):
    """Updates the active API key and saves it to .env."""
    global ACTIVE_GEMINI_KEY
    ACTIVE_GEMINI_KEY = new_key.strip()
    
    # Update .env file
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        content = env_path.read_text(encoding="utf-8")
        if "GEMINI_API_KEY=" in content:
            new_content = re.sub(r"GEMINI_API_KEY=.*", f"GEMINI_API_KEY={ACTIVE_GEMINI_KEY}", content)
        else:
            new_content = content + f"\nGEMINI_API_KEY={ACTIVE_GEMINI_KEY}\n"
        env_path.write_text(new_content, encoding="utf-8")

async def test_gemini_key(api_key: str) -> Tuple[bool, str]:
    """Tests if a Gemini API key is valid."""
    models_to_test = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash"]
    for m in models_to_test:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key.strip()}"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": "Hello! Say: 'Riya is ready!'"}]}]
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    reply = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    return True, reply
        except Exception:
            continue
    return False, "Could not connect to Gemini models with this key."

async def get_ai_reply(chat_id: int, user_id: int, user_name: str, message_text: str) -> str:
    """Generates a reply from Google Gemini with Riya's girl persona, or falls back gracefully."""
    clean_text = re.sub(r"@\w+", "", message_text).strip()
    if not clean_text:
        return f"Hey {user_name}! 🌸 Did you call me? What's on your mind? ✨"

    conv_key = f"{chat_id}_{user_id}"
    history = chat_history.setdefault(conv_key, [])

    if not ACTIVE_GEMINI_KEY:
        return get_fallback_reply(clean_text, user_name)

    # Build contents with short-term history
    contents = []
    for item in history[-MAX_HISTORY_TURNS:]:
        contents.append({
            "role": item["role"],
            "parts": [{"text": item["text"]}]
        })
    
    prompt_with_context = f"[{user_name}]: {clean_text}"
    contents.append({
        "role": "user",
        "parts": [{"text": prompt_with_context}]
    })

    payload = {
        "system_instruction": {
            "parts": [{"text": f"{RIYA_REAL_AI_PROMPT}\nYou are currently talking to {user_name} in chat."}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.88,
            "maxOutputTokens": 300,
            "topP": 0.95
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    models_to_call = ["gemini-3.5-flash", "gemini-3.5-flash-lite", GEMINI_MODEL]
    # De-duplicate while preserving order
    seen = set()
    models_to_call = [x for x in models_to_call if not (x in seen or seen.add(x))]

    for m in models_to_call:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={ACTIVE_GEMINI_KEY}"
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    reply_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    
                    # Store history
                    history.append({"role": "user", "text": clean_text})
                    history.append({"role": "model", "text": reply_text})
                    if len(history) > MAX_HISTORY_TURNS * 2:
                        history = history[-(MAX_HISTORY_TURNS * 2):]
                    chat_history[conv_key] = history
                    
                    return reply_text
                else:
                    logger.warning(f"Model {m} returned status {response.status_code}")
        except Exception as e:
            logger.error(f"Error calling model {m}: {e}")
            continue

    return get_fallback_reply(clean_text, user_name)
