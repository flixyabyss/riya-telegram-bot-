import re
import datetime
from typing import Optional, Tuple, List
from telegram import Update, ChatPermissions
from telegram.constants import ParseMode, ChatMemberStatus, ChatType
from telegram.ext import ContextTypes
from telegram.error import TelegramError, BadRequest
from config import MAX_WARNS_DEFAULT, BOT_NAME, OWNER_IDS
import database as db

async def is_user_admin(chat, user_id: int, context: ContextTypes.DEFAULT_TYPE, sender_chat=None) -> bool:
    """Checks if a user is an administrator, creator, anonymous group admin, or bot owner."""
    if not user_id:
        return False
    if user_id in OWNER_IDS:
        return True
    if user_id == 1087968824:  # Telegram Anonymous Admin ID
        return True
    if sender_chat and sender_chat.id == chat.id:
        return True
    try:
        member = await chat.get_member(user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        return False

async def is_bot_admin(chat, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Checks if the bot itself has administrator rights in the group."""
    try:
        bot_member = await chat.get_member(context.bot.id)
        return bot_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        return False

def parse_time_delta(time_str: str) -> Optional[datetime.timedelta]:
    """Parses duration string like '10m', '2h', '1d' into timedelta."""
    match = re.match(r"^(\d+)([smhd])$", time_str.lower())
    if not match:
        return None
    val, unit = int(match.group(1)), match.group(2)
    if unit == "s":
        return datetime.timedelta(seconds=val)
    elif unit == "m":
        return datetime.timedelta(minutes=val)
    elif unit == "h":
        return datetime.timedelta(hours=val)
    elif unit == "d":
        return datetime.timedelta(days=val)
    return None

async def resolve_target(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Tuple[Optional[int], Optional[str], List[str]]:
    """
    Extracts the target user_id, display_name, and remaining arguments.
    Works by reply, numeric user ID, or @username.
    """
    chat = update.effective_chat
    args = list(context.args or [])
    reply = update.message.reply_to_message

    # 1. Target via reply
    if reply and reply.from_user:
        target_id = reply.from_user.id
        target_name = reply.from_user.mention_html()
        return target_id, target_name, args

    # 2. Target via argument (ID or username)
    if args:
        first_arg = args[0]
        # Numeric ID
        if first_arg.isdigit() or (first_arg.startswith("-") and first_arg[1:].isdigit()):
            target_id = int(first_arg)
            target_name = f"<code>{target_id}</code>"
            try:
                m = await chat.get_member(target_id)
                if m and m.user:
                    target_name = m.user.mention_html()
            except Exception:
                pass
            return target_id, target_name, args[1:]

        # Username @handle
        if first_arg.startswith("@"):
            username = first_arg[1:].lower()
            u = db.get_user_by_username(username)
            if u:
                target_id = u["user_id"]
                target_name = f"@{username}"
                return target_id, target_name, args[1:]
            else:
                return None, f"@{username}", args[1:]

    return None, None, args

# ----------------- MODERATION COMMANDS -----------------

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return

    if not await is_user_admin(chat, user.id, context, sender_chat=update.message.sender_chat):
        await update.message.reply_text("🌸 Aww, only group admins can ban members! 🙈")
        return
    if not await is_bot_admin(chat, context):
        await update.message.reply_text("⚠️ Please grant me Admin rights with ban permissions first! 💖")
        return

    target_id, target_name, remaining_args = await resolve_target(update, context)
    reason = " ".join(remaining_args).strip() or "No reason specified"

    if not target_id:
        if target_name and target_name.startswith("@"):
            await update.message.reply_text(f"🌸 I couldn't find user {target_name} in my records yet! Please reply to their message or provide their numeric User ID.")
        else:
            await update.message.reply_text("🌸 <b>Usage:</b> Reply to someone with <code>/ban [reason]</code> or use <code>/ban [user_id] [reason]</code>!", parse_mode=ParseMode.HTML)
        return

    if target_id == context.bot.id:
        await update.message.reply_text("Aww! Why would you want to ban me? I've been so nice! 🥺💔")
        return

    if await is_user_admin(chat, target_id, context):
        await update.message.reply_text("✨ I cannot ban an administrator! They hold the crown too! 👑")
        return

    try:
        await chat.ban_member(target_id)
        db.reset_warnings(chat.id, target_id)
        await update.message.reply_text(
            f"🔨 <b>Member Banned!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>User:</b> {target_name} [<code>{target_id}</code>]\n"
            f"👮 <b>Admin:</b> {user.mention_html()}\n"
            f"📝 <b>Reason:</b> {reason}\n"
            f"✨ <i>Riya has kept the group safe!</i> 🌸",
            parse_mode=ParseMode.HTML
        )
    except TelegramError as e:
        await update.message.reply_text(f"❌ Failed to ban: {e}")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return

    if not await is_user_admin(chat, user.id, context, sender_chat=update.message.sender_chat):
        await update.message.reply_text("🌸 Only group admins can unban members! 🙈")
        return

    target_id, target_name, _ = await resolve_target(update, context)

    if not target_id:
        await update.message.reply_text("🌸 Reply to a user or use <code>/unban [user_id]</code>!", parse_mode=ParseMode.HTML)
        return

    try:
        await chat.unban_member(target_id)
        await update.message.reply_text(
            f"✨ <b>Member Unbanned!</b>\n"
            f"User {target_name} is now free to rejoin the group! 🌸💖",
            parse_mode=ParseMode.HTML
        )
    except TelegramError as e:
        await update.message.reply_text(f"❌ Could not unban: {e}")

async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return

    if not await is_user_admin(chat, user.id, context, sender_chat=update.message.sender_chat):
        await update.message.reply_text("🌸 Aww, only admins can kick members! ✨")
        return

    target_id, target_name, _ = await resolve_target(update, context)

    if not target_id:
        await update.message.reply_text("🌸 Reply to someone with <code>/kick</code> or provide their User ID!", parse_mode=ParseMode.HTML)
        return

    if await is_user_admin(chat, target_id, context):
        await update.message.reply_text("👑 I cannot kick another admin!")
        return

    try:
        await chat.unban_member(target_id)  # Unbanning after kick allows rejoining
        await update.message.reply_text(
            f"👢 <b>Member Kicked!</b>\n"
            f"Bye bye {target_name}! Behave nicely next time! 🌸👋",
            parse_mode=ParseMode.HTML
        )
    except TelegramError as e:
        await update.message.reply_text(f"❌ Failed to kick: {e}")

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return

    if not await is_user_admin(chat, user.id, context, sender_chat=update.message.sender_chat):
        await update.message.reply_text("🌸 Only admins can mute chat members! ✨")
        return
    if not await is_bot_admin(chat, context):
        await update.message.reply_text("⚠️ Please grant me Admin rights with restrict permissions first! 💖")
        return

    target_id, target_name, remaining_args = await resolve_target(update, context)

    if not target_id:
        await update.message.reply_text("🌸 Reply to someone with <code>/mute [optional time: 10m/2h/1d]</code>!", parse_mode=ParseMode.HTML)
        return

    if await is_user_admin(chat, target_id, context):
        await update.message.reply_text("👑 You cannot mute an admin!")
        return

    duration_str = remaining_args[0] if remaining_args else None
    until_date = None
    time_label = "Indefinitely"
    if duration_str:
        delta = parse_time_delta(duration_str)
        if delta:
            until_date = datetime.datetime.now(datetime.timezone.utc) + delta
            time_label = duration_str

    # ChatPermissions compatible with python-telegram-bot 22+
    permissions = ChatPermissions(
        can_send_messages=False,
        can_send_audios=False,
        can_send_documents=False,
        can_send_photos=False,
        can_send_videos=False,
        can_send_video_notes=False,
        can_send_voice_notes=False,
        can_send_polls=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False
    )

    try:
        await chat.restrict_member(target_id, permissions, until_date=until_date)
        await update.message.reply_text(
            f"🤐 <b>Member Muted!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>User:</b> {target_name}\n"
            f"⏱️ <b>Duration:</b> <code>{time_label}</code>\n"
            f"🤫 <i>Shh... quiet time! Be nice when you return!</i> 🌸",
            parse_mode=ParseMode.HTML
        )
    except TelegramError as e:
        await update.message.reply_text(f"❌ Failed to mute: {e}")

async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return

    if not await is_user_admin(chat, user.id, context, sender_chat=update.message.sender_chat):
        await update.message.reply_text("🌸 Only admins can unmute members! ✨")
        return

    target_id, target_name, _ = await resolve_target(update, context)

    if not target_id:
        await update.message.reply_text("🌸 Reply to someone with <code>/unmute</code> or provide their User ID!", parse_mode=ParseMode.HTML)
        return

    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True
    )

    try:
        await chat.restrict_member(target_id, permissions)
        await update.message.reply_text(
            f"🎉 <b>Member Unmuted!</b>\n"
            f"{target_name} can speak again! Welcome back to the chat! 💖✨",
            parse_mode=ParseMode.HTML
        )
    except TelegramError as e:
        await update.message.reply_text(f"❌ Could not unmute: {e}")

async def warn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return

    if not await is_user_admin(chat, user.id, context, sender_chat=update.message.sender_chat):
        await update.message.reply_text("🌸 Aww, only admins can warn members! ✨")
        return

    target_id, target_name, remaining_args = await resolve_target(update, context)
    reason = " ".join(remaining_args).strip() or "Breaking group rules"

    if not target_id:
        await update.message.reply_text("🌸 Reply to someone with <code>/warn [reason]</code>!", parse_mode=ParseMode.HTML)
        return

    if await is_user_admin(chat, target_id, context):
        await update.message.reply_text("👑 I cannot warn an admin!")
        return

    count = db.add_warning(chat.id, target_id, reason, user.id)

    if count >= MAX_WARNS_DEFAULT:
        try:
            await chat.ban_member(target_id)
            db.reset_warnings(chat.id, target_id)
            await update.message.reply_text(
                f"🚨 <b>Warning Limit Exceeded ({count}/{MAX_WARNS_DEFAULT})!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 {target_name} has received too many warnings and was <b>BANNED</b>!\n"
                f"🌸 <i>Rules are rules, sweetie!</i> 🛡️",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Reached limit, but failed to ban: {e}")
    else:
        await update.message.reply_text(
            f"⚠️ <b>Warning Issued! ({count}/{MAX_WARNS_DEFAULT})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>User:</b> {target_name}\n"
            f"📝 <b>Reason:</b> {reason}\n"
            f"⚠️ <i>Careful! {MAX_WARNS_DEFAULT - count} more strikes and you're out!</i> 🌸",
            parse_mode=ParseMode.HTML
        )

async def warns_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    target_id, target_name, _ = await resolve_target(update, context)
    if not target_id:
        target_id = update.effective_user.id
        target_name = update.effective_user.mention_html()

    count = db.get_warning_count(chat.id, target_id)
    await update.message.reply_text(
        f"📋 <b>Warning Status</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>User:</b> {target_name}\n"
        f"⚠️ <b>Active Strikes:</b> <code>{count}/{MAX_WARNS_DEFAULT}</code> 🌸",
        parse_mode=ParseMode.HTML
    )

async def resetwarns_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if not await is_user_admin(chat, user.id, context, sender_chat=update.message.sender_chat):
        await update.message.reply_text("🌸 Only admins can reset warnings! ✨")
        return

    target_id, target_name, _ = await resolve_target(update, context)

    if not target_id:
        await update.message.reply_text("🌸 Reply to someone with <code>/resetwarns</code> or provide User ID!", parse_mode=ParseMode.HTML)
        return

    db.reset_warnings(chat.id, target_id)
    await update.message.reply_text(
        f"✨ <b>Warnings Cleared!</b>\n"
        f"All strikes for {target_name} have been reset! Fresh start! 🌸💖",
        parse_mode=ParseMode.HTML
    )

async def promote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Promotes a user to group admin."""
    chat = update.effective_chat
    user = update.effective_user
    if not await is_user_admin(chat, user.id, context, sender_chat=update.message.sender_chat):
        await update.message.reply_text("🌸 Only group admins can promote members! ✨")
        return
    if not await is_bot_admin(chat, context):
        await update.message.reply_text("⚠️ I need admin rights to promote others! 💖")
        return

    target_id, target_name, remaining_args = await resolve_target(update, context)
    custom_title = " ".join(remaining_args).strip() if remaining_args else "Admin"

    if not target_id:
        await update.message.reply_text("🌸 <b>Usage:</b> Reply to someone with <code>/promote [optional title]</code>!", parse_mode=ParseMode.HTML)
        return

    try:
        await chat.promote_member(
            user_id=target_id,
            can_change_info=True,
            can_delete_messages=True,
            can_invite_users=True,
            can_restrict_members=True,
            can_pin_messages=True
        )
        if custom_title:
            try:
                await chat.set_administrator_custom_title(target_id, custom_title[:16])
            except Exception:
                pass

        await update.message.reply_text(
            f"👑 <b>Member Promoted!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Admin:</b> {target_name}\n"
            f"🏷️ <b>Title:</b> <code>{custom_title}</code>\n"
            f"✨ <i>Welcome to the admin team! Lead with care!</i> 🌸💖",
            parse_mode=ParseMode.HTML
        )
    except TelegramError as e:
        await update.message.reply_text(f"❌ Failed to promote: {e}")

async def demote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Demotes an admin to normal member."""
    chat = update.effective_chat
    user = update.effective_user
    if not await is_user_admin(chat, user.id, context, sender_chat=update.message.sender_chat):
        await update.message.reply_text("🌸 Only group admins can demote! ✨")
        return

    target_id, target_name, _ = await resolve_target(update, context)

    if not target_id:
        await update.message.reply_text("🌸 <b>Usage:</b> Reply to an admin with <code>/demote</code>!", parse_mode=ParseMode.HTML)
        return

    try:
        await chat.promote_member(
            user_id=target_id,
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False
        )
        await update.message.reply_text(
            f"📉 <b>Member Demoted!</b>\n"
            f"{target_name} is now a regular member again! 🌸",
            parse_mode=ParseMode.HTML
        )
    except TelegramError as e:
        await update.message.reply_text(f"❌ Failed to demote: {e}")

async def del_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if not await is_user_admin(chat, user.id, context, sender_chat=update.message.sender_chat):
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("🌸 Reply to the message you want me to delete!")
        return

    try:
        await update.message.reply_to_message.delete()
        await update.message.delete()
    except Exception as e:
        await update.message.reply_text(f"❌ Could not delete: please ensure I have 'Delete Messages' permission! 🙈")

async def purge_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if not await is_user_admin(chat, user.id, context, sender_chat=update.message.sender_chat):
        await update.message.reply_text("🌸 Only admins can purge messages! ✨")
        return

    reply = update.message.reply_to_message
    args = context.args or []

    # 1. Purge via count (e.g. /purge 15)
    if args and args[0].isdigit():
        count = min(int(args[0]), 100)
        curr_id = update.message.message_id
        from_id = max(1, curr_id - count)
    elif reply:
        # 2. Purge via reply
        from_id = reply.message_id
        curr_id = update.message.message_id
        if curr_id - from_id > 100:
            from_id = curr_id - 100
    else:
        await update.message.reply_text(
            "🌸 <b>Usage:</b>\n"
            "• Reply to a message with <code>/purge</code>\n"
            "• Or specify count: <code>/purge 20</code> (up to 100)",
            parse_mode=ParseMode.HTML
        )
        return

    deleted_count = 0
    for mid in range(from_id, update.message.message_id + 1):
        try:
            await context.bot.delete_message(chat_id=chat.id, message_id=mid)
            deleted_count += 1
        except Exception:
            pass

    status = await chat.send_message(f"🧹 Purged <code>{deleted_count}</code> messages cleanly! ✨", parse_mode=ParseMode.HTML)
    if context.job_queue:
        context.job_queue.run_once(lambda ctx: status.delete(), 4)

async def pin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if not await is_user_admin(chat, user.id, context, sender_chat=update.message.sender_chat):
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("🌸 Reply to a message with <code>/pin</code>!", parse_mode=ParseMode.HTML)
        return

    try:
        await update.message.reply_to_message.pin()
        await update.message.reply_text("📌 Message pinned successfully! ✨")
    except Exception as e:
        await update.message.reply_text(f"❌ Could not pin: {e}")

async def unpin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if not await is_user_admin(chat, user.id, context, sender_chat=update.message.sender_chat):
        return
    try:
        await chat.unpin_message()
        await update.message.reply_text("📌 Pinned message unpinned! 🌸")
    except Exception as e:
        await update.message.reply_text(f"❌ Could not unpin: {e}")

async def pinned_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the currently pinned message."""
    chat = update.effective_chat
    try:
        full_chat = await context.bot.get_chat(chat.id)
        if full_chat.pinned_message:
            link = full_chat.pinned_message.link
            text = (
                f"📌 <b>Currently Pinned Message:</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"{full_chat.pinned_message.text or full_chat.pinned_message.caption or '<i>[Media / Sticker]</i>'}\n\n"
                f"👉 <a href='{link}'>Click here to view original message</a>"
            )
            await update.message.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        else:
            await update.message.reply_text("🌸 No message is currently pinned in this group!")
    except Exception as e:
        await update.message.reply_text(f"❌ Could not fetch pinned message: {e}")

async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    group_settings = db.get_group_settings(chat.id)
    rules = group_settings.get("rules") if group_settings else None

    if not rules:
        await update.message.reply_text("📜 No rules set yet for this group! Admins can set rules with <code>/setrules [text]</code>! 🌸", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(
            f"📜 <b>Rules for {chat.title}</b> 🌸\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{rules}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Please follow these rules and enjoy!</i> 💖",
            parse_mode=ParseMode.HTML
        )

async def setrules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if not await is_user_admin(chat, user.id, context, sender_chat=update.message.sender_chat):
        await update.message.reply_text("🌸 Only group admins can set rules! ✨")
        return

    text = " ".join(context.args).strip()
    if not text:
        await update.message.reply_text("🌸 <b>Usage:</b> <code>/setrules [your group rules here]</code>", parse_mode=ParseMode.HTML)
        return

    db.update_group_setting(chat.id, "rules", text)
    await update.message.reply_text("✅ <b>Group rules updated successfully!</b> 📜🌸", parse_mode=ParseMode.HTML)

async def lock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if not await is_user_admin(chat, user.id, context, sender_chat=update.message.sender_chat):
        return

    if not context.args:
        await update.message.reply_text("🌸 <b>Usage:</b> <code>/lock [links | stickers | media]</code>", parse_mode=ParseMode.HTML)
        return

    l_type = context.args[0].lower()
    if l_type not in ["links", "stickers", "media"]:
        await update.message.reply_text("🌸 You can only lock: <code>links</code>, <code>stickers</code>, or <code>media</code>!", parse_mode=ParseMode.HTML)
        return

    db.set_lock(chat.id, l_type, True)
    await update.message.reply_text(f"🔒 Locked <b>{l_type}</b>! Non-admins will have them deleted! 🛡️✨", parse_mode=ParseMode.HTML)

async def unlock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if not await is_user_admin(chat, user.id, context, sender_chat=update.message.sender_chat):
        return

    if not context.args:
        await update.message.reply_text("🌸 <b>Usage:</b> <code>/unlock [links | stickers | media]</code>", parse_mode=ParseMode.HTML)
        return

    l_type = context.args[0].lower()
    db.set_lock(chat.id, l_type, False)
    await update.message.reply_text(f"🔓 Unlocked <b>{l_type}</b>! Members can send them freely again! 🌸", parse_mode=ParseMode.HTML)

async def locks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    locks = db.get_locked_types(chat.id)
    if not locks:
        await update.message.reply_text("🔓 No restrictions active! Everything is open! 🌸")
    else:
        text = f"🔒 <b>Active Locks in {chat.title}:</b>\n• " + "\n• ".join(locks)
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
