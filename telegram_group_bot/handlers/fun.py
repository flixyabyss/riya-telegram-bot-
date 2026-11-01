import random
import time
from telegram import Update
from telegram.constants import ParseMode, ChatType
from telegram.ext import ContextTypes
import database as db

FLIRT_LINES = [
    "Are you a magician? Because whenever I look at you, everyone else disappears! ✨🙈",
    "Is your name Google? Because you have everything I’ve been searching for! 🌸💖",
    "Do you believe in love at first sight, or should I walk by again? 🎀🥰",
    "Are you made of copper and tellurium? Because you are Cu-Te! 🥺✨",
    "If you were a vegetable, you'd be a cute-cumber! 🥒💖",
    "I'm not a photographer, but I can definitely picture us having a great time together! 📸🌸",
    "Do you have a map? Because I just got lost in your eyes! 💫🙈",
    "Are you Wi-Fi? Because I'm feeling a really strong connection right now! 📶💖"
]

ROAST_LINES = [
    "I’d agree with you, but then we’d both be wrong! 😜💅",
    "You bring everyone so much joy... whenever you leave the room! 🚪✨",
    "I'm not insulting you, I'm just describing you! 🙈🌸",
    "You have an entire life to be pleasant, why not start today? 🤭🎀",
    "I'd give you a nasty look, but it looks like you've already got one! 💁‍♀️✨",
    "Your secrets are always safe with me... I wasn't even listening! 🤫💖"
]

TRUTH_QUESTIONS = [
    "What is the most embarrassing thing you've ever done in front of a crush? 🙈",
    "What is one secret you've never told anyone in this group? 🤫",
    "If you could trade lives with someone in this chat for 24 hours, who would it be and why? ✨",
    "What is your biggest guilty pleasure? 🍰",
    "What is the weirdest habit you have when you're alone? 🌸",
    "Who was your first celebrity crush? 💖"
]

DARE_CHALLENGES = [
    "Change your Telegram bio to 'I love Riya ✨' for 1 hour! 🎀",
    "Send a voice note singing your favorite chorus right now in this chat! 🎤",
    "Send the last photo in your gallery without explaining it! 📸🙈",
    "Compliment the third person above you in this chat! 🌸",
    "Send a funny voice message introducing yourself like an anime character! 🎭"
]

QUOTES = [
    "✨ 'Keep your face always toward the sunshine, and shadows will fall behind you.'",
    "🌸 'Every day may not be good, but there's something good in every day.'",
    "💖 'Be a voice, not an echo. You are uniquely special!'",
    "💫 'Happiness looks gorgeous on you, so wear it every single day!'",
    "🎀 'You are capable of amazing things, believe in yourself!'"
]

async def flirt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = random.choice(FLIRT_LINES)
    await update.message.reply_text(f"🌸 <i>{reply}</i> 🙈💖", parse_mode=ParseMode.HTML)

async def roast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.effective_user.first_name
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user.first_name
    roast = random.choice(ROAST_LINES)
    await update.message.reply_text(f"🔥 Hey <b>{target}</b>, {roast}", parse_mode=ParseMode.HTML)

async def truth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    truth = random.choice(TRUTH_QUESTIONS)
    await update.message.reply_text(
        f"🤫 <b>Truth Time!</b>\n━━━━━━━━━━━━━━━━━━━━━━\n{truth}\n━━━━━━━━━━━━━━━━━━━━━━\n<i>Be 100% honest! No lying!</i> 🌸",
        parse_mode=ParseMode.HTML
    )

async def dare_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dare = random.choice(DARE_CHALLENGES)
    await update.message.reply_text(
        f"🎯 <b>Dare Challenge!</b>\n━━━━━━━━━━━━━━━━━━━━━━\n{dare}\n━━━━━━━━━━━━━━━━━━━━━━\n<i>Do you have the courage to do it? Hehe!</i> 😜✨",
        parse_mode=ParseMode.HTML
    )

async def quote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quote = random.choice(QUOTES)
    await update.message.reply_text(quote)

async def flip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    outcome = random.choice(["Heads 🪙", "Tails 🪙"])
    await update.message.reply_text(f"✨ <i>Flipping the coin...</i>\n\nResult: <b>{outcome}</b>! 🌸", parse_mode=ParseMode.HTML)

async def roll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dice = random.randint(1, 6)
    await update.message.reply_text(f"🎲 <i>Rolling dice...</i>\n\nYou rolled a <b>{dice}</b>! ✨", parse_mode=ParseMode.HTML)

async def ship_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user1 = update.effective_user.first_name
    user2 = None

    if update.message.reply_to_message:
        user2 = update.message.reply_to_message.from_user.first_name
    elif context.args:
        user2 = " ".join(context.args)
    else:
        await update.message.reply_text("🌸 Reply to someone or write their name to ship! <code>/ship @username</code>", parse_mode=ParseMode.HTML)
        return

    # Deterministic or fun random percent based on names
    combined = sorted([user1.lower(), user2.lower()])
    seed = sum(ord(c) for c in "".join(combined))
    random.seed(seed)
    percentage = random.randint(30, 100)
    random.seed() # reset

    filled = int(percentage / 10)
    bar = "💖" * filled + "🤍" * (10 - filled)

    if percentage >= 85:
        comment = "Made for each other! Soulmates alert! 💍✨🥰"
    elif percentage >= 60:
        comment = "Super cute couple vibes! Sparks flying! 🌸💖"
    else:
        comment = "Best friends forever or enemies to lovers? Hehe! 🙈💫"

    text = (
        f"💘 <b>Love Compatibility Match</b> 💘\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>{user1}</b>  +  👤 <b>{user2}</b>\n\n"
        f"📊 <b>Score:</b> {percentage}%\n"
        f"[{bar}]\n\n"
        f"✨ <i>Riya says: {comment}</i>"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def afk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    reason = "Away from keyboard"
    if context.args:
        reason = " ".join(context.args)

    db.set_afk(user.id, reason)
    await update.message.reply_text(
        f"💤 <b>{user.first_name} is now AFK!</b>\n"
        f"📝 <b>Reason:</b> <i>{reason}</i>\n"
        f"🌸 <i>I'll let anyone know if they mention you! Rest well sweetie!</i> ✨",
        parse_mode=ParseMode.HTML
    )

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.effective_user
    chat = update.effective_chat
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    elif context.args and context.args[0].isdigit():
        try:
            target = (await chat.get_member(int(context.args[0]))).user
        except Exception:
            pass

    warn_count = db.get_warning_count(chat.id, target.id)
    username = f"@{target.username}" if target.username else "No username"

    role = "Member 👤"
    if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        try:
            member = await chat.get_member(target.id)
            if member.status == "creator":
                role = "Group Owner 👑"
            elif member.status == "administrator":
                role = "Administrator 🛡️"
        except Exception:
            pass

    text = (
        f"🪪 <b>User Profile Card</b> 🌸\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✨ <b>Name:</b> {target.first_name} {target.last_name or ''}\n"
        f"🆔 <b>User ID:</b> <code>{target.id}</code>\n"
        f"🔗 <b>Username:</b> {username}\n"
        f"🎖️ <b>Role:</b> {role}\n"
        f"⚠️ <b>Warnings:</b> <code>{warn_count}</code> strikes\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✨ <i>Checked by {db.MAX_WARNS_DEFAULT and 'Riya'}</i> 💖"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def chatinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await update.message.reply_text("🌸 This command is for groups only!")
        return

    member_count = await chat.get_member_count()
    username = f"@{chat.username}" if chat.username else "Private Group"

    text = (
        f"ℹ️ <b>Group Information</b> 🌸\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📛 <b>Title:</b> {chat.title}\n"
        f"🆔 <b>Chat ID:</b> <code>{chat.id}</code>\n"
        f"👥 <b>Total Members:</b> <code>{member_count}</code>\n"
        f"🔗 <b>Link/Handle:</b> {username}\n"
        f"🛡️ <b>Type:</b> {chat.type.capitalize()}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Proudly protected by Riya!</i> 🌸💖"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
