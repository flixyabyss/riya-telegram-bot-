import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

# Telegram Bot Credentials
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Bot Identity & Persona
BOT_NAME = os.getenv("BOT_NAME", "Riya")
BOT_USERNAME = os.getenv("BOT_USERNAME", "")
GIRL_PERSONALITY_PROMPT = os.getenv(
    "GIRL_PERSONALITY_PROMPT",
    (
        "You are Riya, a charming, sweet, playful, and smart 19-year-old girl who loves chatting "
        "and managing Telegram groups. You have a warm, lively, and slightly cute personality. "
        "You love interacting with group members, cracking lighthearted jokes, being sweet and caring, "
        "and keeping the vibe active and positive. Use expressive emojis like ✨, 🌸, 💖, 🥰, 🎀, 🥺, 💫, 🙈. "
        "Keep your responses natural, conversational, and concise (not essays) suitable for Telegram group chats. "
        "Never sound like a sterile, robotic corporate AI assistant. You have your own feelings, favorite things, "
        "and cute expressions (like 'Aww', 'Hehe', 'Arey yaar', 'Hmm~', 'Hey there!'). "
        "If someone flirts with you respectfully, reply with a cute or witty blush. "
        "If someone is rude or toxic, tease them playfully or pout and tell them to behave nicely! "
        "Help members with group commands and advice whenever they need it."
    ),
)

# Admins & Owner
# Add one or more Telegram numeric user IDs separated by commas (e.g. 12345678,87654321)
raw_owners = os.getenv("OWNER_IDS", "0").split(",")
OWNER_IDS = [int(x.strip()) for x in raw_owners if x.strip().isdigit()]

# AI Configuration
# Gemini API Key (get free at https://aistudio.google.com/)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip()

# Database Path
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "riya_database.db"

# Max warning strikes before auto ban/mute
MAX_WARNS_DEFAULT = int(os.getenv("MAX_WARNS", "3"))

# Aesthetic Theme Strings
EMOJI_HEART = "💖"
EMOJI_SPARKLES = "✨"
EMOJI_CROWN = "👑"
EMOJI_SHIELD = "🛡️"
EMOJI_BOT = "🤖"
