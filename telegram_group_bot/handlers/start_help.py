import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode, ChatType
from telegram.ext import ContextTypes
from config import BOT_NAME, OWNER_IDS
import database as db

START_TIME = time.time()

def get_start_keyboard(bot_username: str) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("➕ Add Me To Your Group 🌸", url=f"https://t.me/{bot_username}?startgroup=true")
        ],
        [
            InlineKeyboardButton("📖 Help & Commands ✨", callback_data="help_main"),
            InlineKeyboardButton("💬 Talk With Me 💖", callback_data="help_ai")
        ],
        [
            InlineKeyboardButton("👑 Owner / Admin 🛡️", callback_data="help_admin"),
            InlineKeyboardButton("🎮 Fun & Games 🎲", callback_data="help_fun")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_help_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("👑 Group Admin", callback_data="help_admin"),
            InlineKeyboardButton("🛡️ Moderation", callback_data="help_mod")
        ],
        [
            InlineKeyboardButton("💬 AI Chat & Persona", callback_data="help_ai"),
            InlineKeyboardButton("🎮 Fun & Games", callback_data="help_fun")
        ],
        [
            InlineKeyboardButton("📌 Notes & Rules", callback_data="help_notes"),
            InlineKeyboardButton("📢 Broadcast & Tools", callback_data="help_bcast")
        ],
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data="help_home")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Help Menu", callback_data="help_main")]])

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    
    # Register user in database
    db.register_user(user.id, user.username, user.first_name)
    
    bot_user = await context.bot.get_me()
    bot_username = bot_user.username

    if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        db.register_group(chat.id, chat.title, chat.type)
        text = (
            f"✨ <b>Heeey everyone! I'm {BOT_NAME}!</b> 🌸\n\n"
            f"I'm so excited to be here in <b>{chat.title}</b>! "
            f"I'll keep this group safe, active, and fun! 🥰\n\n"
            f"• Mention me or reply to any of my messages to talk with me! 💬\n"
            f"• Type <code>/help</code> to see all my moderation and fun commands! 🛡️\n\n"
            f"<i>Make sure to make me an admin with ban/delete permissions so I can protect you all!</i> 💖"
        )
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📖 See Help Menu ✨", url=f"https://t.me/{bot_username}?start=help")]
            ])
        )
    else:
        text = (
            f"🌸 <b>Hiii {user.first_name}! I'm {BOT_NAME}</b> 💖\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✨ <i>Your friendly group manager & sweet AI companion!</i>\n\n"
            f"🌟 <b>What I Can Do For You:</b>\n"
            f"• <b>Group Protection:</b> Ban, Kick, Mute, Warn, Anti-Link & Locks\n"
            f"• <b>Cute AI Chat:</b> Mention me or reply to chat with me anytime!\n"
            f"• <b>Aesthetic Welcomes:</b> Gorgeous greeting cards for new members\n"
            f"• <b>Broadcast System:</b> Broadcast messages across all connected groups\n"
            f"• <b>Fun Activities:</b> Games, AFK system, quotes, love meter & more!\n\n"
            f"👉 <i>Click the buttons below to explore everything!</i>"
        )
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_start_keyboard(bot_username)
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"🌸 <b>{BOT_NAME}'s Command Center</b> ✨\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Choose a category below to explore all my features and powers! 💖"
    )
    if update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=get_help_keyboard()
            )
        except Exception:
            pass
    else:
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_help_keyboard()
        )

async def help_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    bot_user = await context.bot.get_me()

    if data == "help_home":
        user = update.effective_user
        text = (
            f"🌸 <b>Hiii {user.first_name}! I'm {BOT_NAME}</b> 💖\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✨ <i>Your friendly group manager & sweet AI companion!</i>\n\n"
            f"👉 <i>Click below to explore commands or add me to your group!</i>"
        )
        try:
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=get_start_keyboard(bot_user.username)
            )
        except Exception:
            pass
        return

    if data == "help_main":
        await help_command(update, context)
        return

    if data == "help_admin":
        text = (
            f"👑 <b>Admin & Management Commands</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• <code>/pin</code> - Pin a message (reply to it)\n"
            f"• <code>/unpin</code> - Unpin the current pinned message\n"
            f"• <code>/pinned</code> - View the currently pinned message\n"
            f"• <code>/del</code> - Delete a message (reply to it)\n"
            f"• <code>/purge [count]</code> - Delete up to 100 recent messages\n"
            f"• <code>/promote [reply]</code> - Promote user to group admin\n"
            f"• <code>/demote [reply]</code> - Demote an admin to normal member\n"
            f"• <code>/setrules [text]</code> - Set custom group rules\n"
            f"• <code>/settings</code> - Open interactive group settings panel\n\n"
            f"<i>Only group admins can use these commands!</i> ✨"
        )
    elif data == "help_mod":
        text = (
            f"🛡️ <b>Moderation & Security Commands</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• <code>/ban [reply/id] [reason]</code> - Ban a member from the group\n"
            f"• <code>/unban [reply/id]</code> - Unban a user\n"
            f"• <code>/kick [reply/id]</code> - Kick a member from the group\n"
            f"• <code>/mute [reply/id] [time]</code> - Mute user (e.g. <code>10m</code>, <code>2h</code>, <code>1d</code>)\n"
            f"• <code>/unmute [reply/id]</code> - Unmute a user\n"
            f"• <code>/warn [reply/id] [reason]</code> - Warn a user (3 warns = auto ban)\n"
            f"• <code>/warns [reply/id]</code> - Check user warnings\n"
            f"• <code>/resetwarns [reply/id]</code> - Clear warnings for a user\n"
            f"• <code>/lock [type]</code> - Lock: <code>links</code>, <code>stickers</code>, <code>media</code>\n"
            f"• <code>/unlock [type]</code> - Unlock specified type\n"
            f"• <code>/locks</code> - View current lock status in this group"
        )
    elif data == "help_ai":
        text = (
            f"💬 <b>AI Chat & Persona Features</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✨ <i>I'm not just a boring bot, I love talking to you!</i>\n\n"
            f"• <b>In Groups:</b>\n"
            f"  - Mention my name: <i>\"Hey Riya, how are you today?\"</i>\n"
            f"  - Reply to any of my messages to continue our conversation!\n"
            f"  - Tag me: <code>@{bot_user.username} tell me a secret</code>\n\n"
            f"• <b>In Private (DM):</b>\n"
            f"  - Just text me directly anytime, I reply instantly! 🥰\n\n"
            f"• <b>Smart Context:</b> I remember recent conversation context so chatting feels real and engaging! 🌸"
        )
    elif data == "help_fun":
        text = (
            f"🎮 <b>Fun & Interactive Commands</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• <code>/afk [reason]</code> - Go AFK! I'll tell anyone who tags you 💤\n"
            f"• <code>/flirt</code> - Get a cute sweet compliment or pick-up line 🙈\n"
            f"• <code>/roast [reply]</code> - Playfully roast someone wittily 😜\n"
            f"• <code>/ship [reply]</code> - Calculate love match percentage! 💘\n"
            f"• <code>/truth</code> - Get an interesting truth question 🤫\n"
            f"• <code>/dare</code> - Get an exciting dare! 🎯\n"
            f"• <code>/flip</code> - Flip a coin (Heads/Tails) 🪙\n"
            f"• <code>/roll</code> - Roll a lucky 6-sided dice 🎲\n"
            f"• <code>/quote</code> - Get a cute inspiring quote ✨"
        )
    elif data == "help_notes":
        text = (
            f"📌 <b>Notes & Filter System</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• <code>#word</code> or <code>/get [word]</code> - Retrieve a saved note\n"
            f"• <code>/save [word] [reply/content]</code> - Save note or media in this group\n"
            f"• <code>/clear [word]</code> - Remove a saved note\n"
            f"• <code>/notes</code> - List all saved notes in this group\n"
            f"• <code>/rules</code> - View group rules\n"
            f"• <code>/setrules [text]</code> - Set custom group rules"
        )
    elif data == "help_bcast":
        text = (
            f"📢 <b>Admin Broadcast & Tools</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• <code>/broadcast [message]</code> (or <code>/bcast</code>)\n"
            f"  <i>Restricted strictly to Bot Owner/Admin!</i>\n"
            f"  Broadcasts your message or forwarded media to <b>EVERY GROUP</b> the bot is added to!\n\n"
            f"• <code>/broadcast -pin [message]</code>\n"
            f"  Broadcasts and automatically pins the message in every group!\n\n"
            f"• <code>/ping</code> - Check bot response speed ⚡\n"
            f"• <code>/stats</code> - Global bot statistics 📊\n"
            f"• <code>/info [reply]</code> - Check user details and ID card 🪪\n"
            f"• <code>/chatinfo</code> - Group information overview ℹ️"
        )
    else:
        text = "Select a category below:"

    try:
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_back_keyboard()
        )
    except Exception:
        pass

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start = time.time()
    msg = await update.message.reply_text("🌸 <i>Checking speed...</i>", parse_mode=ParseMode.HTML)
    latency = round((time.time() - start) * 1000, 2)
    uptime_sec = int(time.time() - START_TIME)
    hours, remainder = divmod(uptime_sec, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    await msg.edit_text(
        f"⚡ <b>Pong!</b> <code>{latency}ms</code> ✨\n"
        f"🌸 <b>Status:</b> All systems bubbly & running smoothly!\n"
        f"⏱️ <b>Uptime:</b> {hours}h {minutes}m {seconds}s 💖",
        parse_mode=ParseMode.HTML
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = db.get_total_stats()
    uptime_sec = int(time.time() - START_TIME)
    hours, remainder = divmod(uptime_sec, 3600)
    minutes, _ = divmod(remainder, 60)

    text = (
        f"📊 <b>{BOT_NAME}'s Global Statistics</b> 🌸\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏘️ <b>Active Groups:</b> <code>{stats['groups']}</code>\n"
        f"👤 <b>Total Users Tracked:</b> <code>{stats['users']}</code>\n"
        f"⏱️ <b>Bot Uptime:</b> <code>{hours}h {minutes}m</code>\n"
        f"💖 <b>Mood:</b> Super happy & helpful! ✨\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Managing with love & power!</i> 🎀"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
