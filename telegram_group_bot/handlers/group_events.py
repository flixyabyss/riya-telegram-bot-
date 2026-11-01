import time
import re
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode, ChatType
from telegram.ext import ContextTypes
from config import BOT_NAME
import database as db
from handlers.admin_mod import is_user_admin

async def on_chat_member_updated(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detects when bot is added or removed from a group."""
    result = update.my_chat_member
    if not result:
        return

    chat = result.chat
    new_status = result.new_chat_member.status

    if new_status in ["member", "administrator"]:
        # Bot added or promoted
        db.register_group(chat.id, chat.title, chat.type)
        try:
            bot_user = await context.bot.get_me()
            welcome_text = (
                f"🌸 <b>Hiii everyone! I'm {BOT_NAME}!</b> ✨\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Thank you for adding me to <b>{chat.title}</b>! 💖\n\n"
                f"🛡️ <i>Please promote me to <b>Admin</b> so I can:</i>\n"
                f"• Welcome new cuties with cute cards 🌸\n"
                f"• Protect this group from spammers and links 🚫\n"
                f"• Chat with all of you when you mention me! 💬\n\n"
                f"Type <code>/help</code> or tap below to see all my powers!"
            )
            await chat.send_message(
                welcome_text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📖 Help & Setup ✨", url=f"https://t.me/{bot_user.username}?start=help")]
                ])
            )
        except Exception:
            pass
    elif new_status in ["left", "kicked"]:
        # Bot removed
        db.set_group_active(chat.id, False)

async def on_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Greets new members who join the group."""
    chat = update.effective_chat
    settings = db.get_group_settings(chat.id)
    
    # Check if welcome is enabled
    if settings and not settings.get("welcome_enabled", 1):
        return

    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            continue

        db.register_user(member.id, member.username, member.first_name)
        count = await chat.get_member_count()

        welcome_card = (
            f"🌸 <b>Welcome to {chat.title}!</b> 💖\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✨ <b>Hello:</b> {member.mention_html()}\n"
            f"🆔 <b>User ID:</b> <code>{member.id}</code>\n"
            f"👥 <b>You are member #{count}!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎀 <i>Be nice, follow the rules, and make great memories here!</i>\n"
            f"💬 <i>Need anything? Just mention Riya!</i> 🌸"
        )

        buttons = []
        if settings and settings.get("rules"):
            buttons.append([InlineKeyboardButton("📜 Group Rules", callback_data="show_rules")])

        try:
            await update.message.reply_text(
                welcome_card,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
            )
        except Exception:
            pass

async def on_left_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a sweet goodbye message."""
    member = update.message.left_chat_member
    if member.id == context.bot.id:
        return
    try:
        await update.message.reply_text(
            f"👋 <b>Bye bye, {member.first_name}!</b> 🥺🌸\n"
            f"<i>We'll miss you in the chat! Take care!</i> 💖",
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass

async def check_locks_and_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inspects messages for active locks, AFK status, and notes trigger."""
    message = update.message
    if not message:
        return

    user = update.effective_user
    chat = update.effective_chat

    # Track user
    if user:
        db.register_user(user.id, user.username, user.first_name)

    # 1. Check if the sender is currently marked as AFK
    if user:
        afk_info = db.get_afk(user.id)
        if afk_info:
            db.remove_afk(user.id)
            duration = int(time.time() - afk_info["afk_time"])
            mins, secs = divmod(duration, 60)
            hours, mins = divmod(mins, 60)
            time_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m {secs}s"
            try:
                await message.reply_text(
                    f"✨ <b>Welcome back {user.first_name}!</b> 🌸\n"
                    f"I have removed your AFK status! (You were away for <code>{time_str}</code>) 💖",
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                pass

    # 2. Check if message replies to or mentions an AFK user
    if message.reply_to_message and message.reply_to_message.from_user:
        replied_user = message.reply_to_message.from_user
        afk_info = db.get_afk(replied_user.id)
        if afk_info:
            duration = int(time.time() - afk_info["afk_time"])
            mins, _ = divmod(duration, 60)
            await message.reply_text(
                f"💤 <b>{replied_user.first_name} is currently AFK!</b>\n"
                f"📝 <b>Reason:</b> <i>{afk_info['reason']}</i>\n"
                f"⏱️ <b>Away for:</b> <code>{mins} minutes</code> 🌸",
                parse_mode=ParseMode.HTML
            )

    # 3. If in group, check locks enforcement
    if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP] and user:
        # Admins bypass locks
        if not await is_user_admin(chat, user.id, context, sender_chat=update.message.sender_chat):
            # Check Sticker Lock
            if message.sticker and db.is_locked(chat.id, "stickers"):
                try:
                    await message.delete()
                    return
                except Exception:
                    pass

            # Check Media Lock
            if (message.photo or message.video or message.audio or message.voice or message.document) and db.is_locked(chat.id, "media"):
                try:
                    await message.delete()
                    return
                except Exception:
                    pass

            # Check Links Lock & Anti-Link
            settings = db.get_group_settings(chat.id)
            anti_link = settings.get("anti_link_enabled", 0) if settings else 0
            if (db.is_locked(chat.id, "links") or anti_link) and message.text:
                if re.search(r"(https?://|t\.me/|telegram\.me/)", message.text, re.IGNORECASE):
                    try:
                        await message.delete()
                        warn_msg = await chat.send_message(
                            f"🚫 {user.mention_html()}, links are locked in this group! 🌸",
                            parse_mode=ParseMode.HTML
                        )
                        return
                    except Exception:
                        pass

    # 4. Check for Notes Trigger (#keyword)
    if message.text and chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        words = message.text.split()
        for word in words:
            if word.startswith("#") and len(word) > 1:
                keyword = word[1:].lower()
                note = db.get_note(chat.id, keyword)
                if note:
                    if note["file_id"]:
                        m_type = note["media_type"]
                        if m_type == "photo":
                            await message.reply_photo(photo=note["file_id"], caption=note["content"], parse_mode=ParseMode.HTML)
                        elif m_type == "video":
                            await message.reply_video(video=note["file_id"], caption=note["content"], parse_mode=ParseMode.HTML)
                        elif m_type == "sticker":
                            await message.reply_sticker(sticker=note["file_id"])
                        else:
                            await message.reply_document(document=note["file_id"], caption=note["content"], parse_mode=ParseMode.HTML)
                    else:
                        await message.reply_text(note["content"], parse_mode=ParseMode.HTML)
                    break
