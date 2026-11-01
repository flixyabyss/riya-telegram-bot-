import re
from telegram import Update
from telegram.constants import ChatType, ChatAction, ParseMode
from telegram.ext import ContextTypes
import database as db
from ai_chat import get_ai_reply, set_gemini_api_key, test_gemini_key, ACTIVE_GEMINI_KEY
from config import BOT_NAME, OWNER_IDS

async def setai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to configure or test the Google Gemini API key."""
    user = update.effective_user
    if user.id not in OWNER_IDS:
        await update.message.reply_text("🌸 Arey yaar, only bot owners can configure the AI key! 🙈")
        return

    if not context.args:
        status = "✅ Connected to Google Gemini" if ACTIVE_GEMINI_KEY else "⚠️ Offline (Using cute built-in fallback)"
        await update.message.reply_text(
            f"🤖 <b>Gemini AI Configuration</b> 🌸\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📡 <b>Status:</b> {status}\n\n"
            f"💡 <b>To connect Gemini:</b>\n"
            f"1. Grab a free API key from https://aistudio.google.com/\n"
            f"2. Send: <code>/setai YOUR_GEMINI_KEY</code>\n\n"
            f"<i>Once connected, Riya chats with authentic Google Gemini AI brains!</i> ✨💖",
            parse_mode=ParseMode.HTML
        )
        return

    api_key = context.args[0].strip()
    loading = await update.message.reply_text(
        "🌸 <i>Connecting to Google Gemini AI and testing your key...</i>",
        parse_mode=ParseMode.HTML
    )

    success, msg = await test_gemini_key(api_key)
    if success:
        set_gemini_api_key(api_key)
        # Try to delete the user's message containing the raw API key for privacy
        try:
            await update.message.delete()
        except Exception:
            pass

        await loading.edit_text(
            f"🎉 <b>Google Gemini Connected Successfully!</b> 🌸\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✨ <b>Model:</b> <code>gemini-1.5-flash</code>\n"
            f"💬 <b>Test Voice:</b> <i>\"{msg}\"</i>\n\n"
            f"🧠 <b>Riya is now thinking with REAL Google Gemini AI!</b>\n"
            f"Mention her or reply to her to experience the conversation! 💖💫",
            parse_mode=ParseMode.HTML
        )
    else:
        await loading.edit_text(
            f"❌ <b>Connection Failed!</b>\n"
            f"Google Gemini rejected this key:\n"
            f"<code>{msg}</code>\n\n"
            f"Please verify your key at https://aistudio.google.com/ and try again! 🥺",
            parse_mode=ParseMode.HTML
        )

async def ai_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    # Ignore command messages
    if message.text.startswith("/"):
        return

    chat = update.effective_chat
    user = update.effective_user
    bot = context.bot
    bot_info = await bot.get_me()
    bot_username = bot_info.username.lower() if bot_info.username else ""

    text = message.text.strip()
    should_reply = False

    # 1. In Private Chat (DM)
    if chat.type == ChatType.PRIVATE:
        should_reply = True

    # 2. In Group / Supergroup
    elif chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        settings = db.get_group_settings(chat.id)
        if settings and settings.get("ai_chat_enabled", 1) == 0:
            return  # AI chat is disabled in this group

        # Reply to bot's message
        if message.reply_to_message and message.reply_to_message.from_user:
            if message.reply_to_message.from_user.id == bot.id:
                should_reply = True

        # Bot tag or name mentioned
        lower_text = text.lower()
        if f"@{bot_username}" in lower_text or re.search(r"\b(riya|ariya)\b", lower_text, re.IGNORECASE):
            should_reply = True

    if should_reply:
        # Show typing action so it feels like a real girl typing
        try:
            await chat.send_action(action=ChatAction.TYPING)
        except Exception:
            pass

        user_name = user.first_name if user else "Friend"
        reply_text = await get_ai_reply(
            chat_id=chat.id,
            user_id=user.id if user else 0,
            user_name=user_name,
            message_text=text
        )

        try:
            await message.reply_text(reply_text)
        except Exception:
            try:
                await chat.send_message(reply_text)
            except Exception:
                pass
