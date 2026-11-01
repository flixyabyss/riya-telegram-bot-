from telegram import Update
from telegram.constants import ParseMode, ChatType
from telegram.ext import ContextTypes
import database as db
from handlers.admin_mod import is_user_admin

async def save_note_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return

    if not await is_user_admin(chat, user.id, context, sender_chat=update.message.sender_chat):
        await update.message.reply_text("🌸 Only group admins can save notes! ✨")
        return

    if not context.args:
        await update.message.reply_text(
            "🌸 <b>Usage:</b>\n"
            "• <code>/save [word] [content]</code>\n"
            "• Or reply to any media/photo with <code>/save [word]</code>!",
            parse_mode=ParseMode.HTML
        )
        return

    keyword = context.args[0].lower().replace("#", "")
    content = " ".join(context.args[1:]).strip()
    file_id = None
    media_type = "text"

    reply = update.message.reply_to_message
    if reply:
        if reply.photo:
            file_id = reply.photo[-1].file_id
            media_type = "photo"
            content = content or reply.caption or ""
        elif reply.video:
            file_id = reply.video.file_id
            media_type = "video"
            content = content or reply.caption or ""
        elif reply.sticker:
            file_id = reply.sticker.file_id
            media_type = "sticker"
        elif reply.document:
            file_id = reply.document.file_id
            media_type = "document"
            content = content or reply.caption or ""
        elif reply.text and not content:
            content = reply.text

    if not content and not file_id:
        await update.message.reply_text("🌸 Please provide some text or reply to media to save!")
        return

    db.set_note(chat.id, keyword, content, file_id, media_type)
    await update.message.reply_text(
        f"✅ <b>Note Saved!</b> 📌\n"
        f"Keyword: <code>#{keyword}</code>\n"
        f"Members can access it by sending <code>#{keyword}</code> or <code>/get {keyword}</code>! 🌸",
        parse_mode=ParseMode.HTML
    )

async def get_note_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not context.args:
        await update.message.reply_text("🌸 <b>Usage:</b> <code>/get [keyword]</code>", parse_mode=ParseMode.HTML)
        return

    keyword = context.args[0].lower().replace("#", "")
    note = db.get_note(chat.id, keyword)

    if not note:
        await update.message.reply_text(f"🌸 Note <code>#{keyword}</code> not found in this group!", parse_mode=ParseMode.HTML)
        return

    if note["file_id"]:
        m_type = note["media_type"]
        if m_type == "photo":
            await update.message.reply_photo(photo=note["file_id"], caption=note["content"], parse_mode=ParseMode.HTML)
        elif m_type == "video":
            await update.message.reply_video(video=note["file_id"], caption=note["content"], parse_mode=ParseMode.HTML)
        elif m_type == "sticker":
            await update.message.reply_sticker(sticker=note["file_id"])
        else:
            await update.message.reply_document(document=note["file_id"], caption=note["content"], parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(note["content"], parse_mode=ParseMode.HTML)

async def clear_note_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if not await is_user_admin(chat, user.id, context, sender_chat=update.message.sender_chat):
        await update.message.reply_text("🌸 Only group admins can delete notes! ✨")
        return

    if not context.args:
        await update.message.reply_text("🌸 <b>Usage:</b> <code>/clear [keyword]</code>", parse_mode=ParseMode.HTML)
        return

    keyword = context.args[0].lower().replace("#", "")
    deleted = db.delete_note(chat.id, keyword)

    if deleted:
        await update.message.reply_text(f"🗑️ Note <code>#{keyword}</code> has been deleted! 🌸", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(f"🌸 Note <code>#{keyword}</code> was not found!", parse_mode=ParseMode.HTML)

async def list_notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    notes = db.get_all_notes(chat.id)

    if not notes:
        await update.message.reply_text("🌸 No saved notes found in this group yet!", parse_mode=ParseMode.HTML)
        return

    formatted_list = "\n".join([f"• <code>#{k}</code>" for k in notes])
    text = (
        f"📌 <b>Saved Notes in {chat.title}:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{formatted_list}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Type <code>#notename</code> or <code>/get notename</code> to view any note!</i> ✨"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
