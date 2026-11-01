from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode, ChatType
from telegram.ext import ContextTypes
import database as db
from handlers.admin_mod import is_user_admin

def build_settings_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    settings = db.get_group_settings(chat_id) or {}
    welcome_on = settings.get("welcome_enabled", 1) == 1
    ai_on = settings.get("ai_chat_enabled", 1) == 1
    antilink_on = settings.get("anti_link_enabled", 0) == 1

    keyboard = [
        [
            InlineKeyboardButton(
                f"🌸 Welcome Greetings: {'✅ ON' if welcome_on else '❌ OFF'}",
                callback_data=f"set_toggle_welcome_{chat_id}"
            )
        ],
        [
            InlineKeyboardButton(
                f"💬 AI Companion Chat: {'✅ ON' if ai_on else '❌ OFF'}",
                callback_data=f"set_toggle_ai_{chat_id}"
            )
        ],
        [
            InlineKeyboardButton(
                f"🔗 Anti-Link Filter: {'✅ ON' if antilink_on else '❌ OFF'}",
                callback_data=f"set_toggle_antilink_{chat_id}"
            )
        ],
        [
            InlineKeyboardButton("❌ Close Menu", callback_data=f"set_close_{chat_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await update.message.reply_text("🌸 Settings can only be configured inside groups!")
        return

    if not await is_user_admin(chat, user.id, context, sender_chat=update.message.sender_chat):
        await update.message.reply_text("🌸 Only group admins can modify group settings! 🙈")
        return

    text = (
        f"⚙️ <b>Group Settings Dashboard: {chat.title}</b> 🌸\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Tap the buttons below to toggle features for this group:"
    )
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=build_settings_keyboard(chat.id)
    )

async def settings_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user = update.effective_user
    chat = update.effective_chat

    if not data.startswith("set_"):
        return

    # Check admin
    if not await is_user_admin(chat, user.id, context):
        await query.answer("🌸 You must be an admin to change settings!", show_alert=True)
        return

    parts = data.split("_")
    action = parts[1] # toggle or close
    
    if action == "close":
        await query.answer()
        await query.message.delete()
        return

    target_setting = parts[2]
    chat_id = int(parts[3])

    settings = db.get_group_settings(chat_id) or {}

    if target_setting == "welcome":
        current = settings.get("welcome_enabled", 1)
        db.update_group_setting(chat_id, "welcome_enabled", 0 if current else 1)
        await query.answer("🌸 Welcome message toggled!")
    elif target_setting == "ai":
        current = settings.get("ai_chat_enabled", 1)
        db.update_group_setting(chat_id, "ai_chat_enabled", 0 if current else 1)
        await query.answer("💬 AI Chat toggled!")
    elif target_setting == "antilink":
        current = settings.get("anti_link_enabled", 0)
        db.update_group_setting(chat_id, "anti_link_enabled", 0 if current else 1)
        await query.answer("🔗 Anti-Link toggled!")

    # Update keyboard
    try:
        await query.edit_message_reply_markup(reply_markup=build_settings_keyboard(chat_id))
    except Exception:
        pass
