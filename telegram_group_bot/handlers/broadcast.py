import asyncio
import time
from telegram import Update
from telegram.constants import ParseMode, ChatType
from telegram.ext import ContextTypes
from telegram.error import TelegramError, Forbidden, BadRequest
from config import OWNER_IDS, BOT_NAME
import database as db

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Check if user is in OWNER_IDS
    if user.id not in OWNER_IDS:
        await update.message.reply_text(
            f"❌ <b>Access Denied!</b>\n"
            f"Arey yaar, this command is strictly reserved for my owner/admin! 🙈🌸\n"
            f"<i>Your User ID:</i> <code>{user.id}</code>",
            parse_mode=ParseMode.HTML
        )
        return

    # Check broadcast targets
    pin_message = False
    args = context.args or []
    
    # Check flags
    if "-pin" in args:
        pin_message = True
        args.remove("-pin")

    target_groups = db.get_all_active_groups()
    if not target_groups:
        await update.message.reply_text(
            "⚠️ <b>No active groups found in database yet!</b>\n"
            "Add me to some groups first so I can broadcast to them! 🌸",
            parse_mode=ParseMode.HTML
        )
        return

    reply_to = update.message.reply_to_message
    broadcast_text = " ".join(args).strip()

    if not reply_to and not broadcast_text:
        await update.message.reply_text(
            "📢 <b>How to use Broadcast:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "• <code>/bcast [your message text]</code>\n"
            "• <code>/bcast -pin [your message]</code> (pins the broadcast in groups)\n"
            "• Reply to any photo/video/forwarded message with <code>/bcast</code> to broadcast that media!\n\n"
            f"<i>Currently connected to {len(target_groups)} group(s).</i> ✨",
            parse_mode=ParseMode.HTML
        )
        return

    status_msg = await update.message.reply_text(
        f"🌸 <b>Starting Broadcast...</b>\n"
        f"🎯 <b>Target:</b> {len(target_groups)} groups\n"
        f"⏳ <i>Please wait while Riya delivers your message...</i>",
        parse_mode=ParseMode.HTML
    )

    start_time = time.time()
    successful = 0
    failed = 0
    total = len(target_groups)

    for idx, chat_id in enumerate(target_groups):
        try:
            sent_msg = None
            if reply_to:
                # Forward or copy message
                sent_msg = await reply_to.copy(chat_id=chat_id)
            else:
                formatted_text = (
                    f"📢 <b>Announcement from Admin</b> ✨\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{broadcast_text}\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"<i>— Delivered with 💖 by {BOT_NAME}</i>"
                )
                sent_msg = await context.bot.send_message(
                    chat_id=chat_id,
                    text=formatted_text,
                    parse_mode=ParseMode.HTML
                )

            if pin_message and sent_msg:
                try:
                    await context.bot.pin_chat_message(chat_id=chat_id, message_id=sent_msg.message_id, disable_notification=False)
                except Exception:
                    pass

            successful += 1

        except Forbidden:
            # Bot was kicked or lacks rights
            failed += 1
            db.set_group_active(chat_id, False)
        except BadRequest as e:
            failed += 1
            if "chat not found" in str(e).lower() or "group chat was migrated" in str(e).lower():
                db.set_group_active(chat_id, False)
        except TelegramError:
            failed += 1

        # Rate limit prevention: small delay between group sends
        await asyncio.sleep(0.08)

        # Update status message every 15 groups or on completion
        if (idx + 1) % 15 == 0 or (idx + 1) == total:
            try:
                await status_msg.edit_text(
                    f"🌸 <b>Broadcasting in progress...</b>\n"
                    f"📊 <b>Progress:</b> {idx + 1}/{total} groups\n"
                    f"✅ <b>Success:</b> {successful} | ❌ <b>Failed:</b> {failed}",
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                pass

    elapsed = round(time.time() - start_time, 2)
    final_report = (
        f"🎉 <b>Broadcast Completed!</b> 🌸\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Total Groups:</b> <code>{total}</code>\n"
        f"✅ <b>Delivered Successfully:</b> <code>{successful}</code>\n"
        f"❌ <b>Failed / Inactive:</b> <code>{failed}</code>\n"
        f"⏱️ <b>Time Taken:</b> <code>{elapsed}s</code>\n"
        f"📌 <b>Pinned:</b> {'Yes' if pin_message else 'No'}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✨ <i>All active groups have been updated!</i> 💖"
    )
    await status_msg.edit_text(final_report, parse_mode=ParseMode.HTML)
