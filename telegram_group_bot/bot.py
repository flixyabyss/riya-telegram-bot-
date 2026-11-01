import logging
import sys
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ChatMemberHandler,
    filters,
    ContextTypes
)

from config import BOT_TOKEN, BOT_NAME
import database as db

# Handlers
from handlers.start_help import (
    start_command,
    help_command,
    help_callback_handler,
    ping_command,
    stats_command
)
from handlers.broadcast import broadcast_command
from handlers.admin_mod import (
    ban_command,
    unban_command,
    kick_command,
    mute_command,
    unmute_command,
    warn_command,
    warns_command,
    resetwarns_command,
    del_command,
    purge_command,
    pin_command,
    unpin_command,
    pinned_command,
    promote_command,
    demote_command,
    rules_command,
    setrules_command,
    lock_command,
    unlock_command,
    locks_command
)
from handlers.fun import (
    flirt_command,
    roast_command,
    truth_command,
    dare_command,
    quote_command,
    flip_command,
    roll_command,
    ship_command,
    afk_command,
    info_command,
    chatinfo_command
)
from handlers.notes import (
    save_note_command,
    get_note_command,
    clear_note_command,
    list_notes_command
)
from handlers.settings import (
    settings_command,
    settings_callback_handler
)
from handlers.group_events import (
    on_chat_member_updated,
    on_new_members,
    on_left_member,
    check_locks_and_afk
)
from handlers.chat_ai import ai_message_handler, setai_command

# Logging setup
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("RiyaBot")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by Updates."""
    logger.error("Exception while handling an update: %s", context.error)

def main():
    if not BOT_TOKEN:
        print("\n" + "="*60)
        print("❌ ERROR: BOT_TOKEN is not set in your .env file!")
        print("Please edit .env and paste your Telegram bot token from @BotFather.")
        print("Example:")
        print("BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ")
        print("="*60 + "\n")
        sys.exit(1)

    # Initialize Database
    logger.info("Initializing database...")
    db.init_db()

    # Build Telegram Bot Application
    logger.info(f"Starting {BOT_NAME}...")
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # 1. Base / Help Commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ping", ping_command))
    application.add_handler(CommandHandler("stats", stats_command))

    # 2. Owner Broadcast & AI Config Commands
    application.add_handler(CommandHandler(["broadcast", "bcast"], broadcast_command))
    application.add_handler(CommandHandler("setai", setai_command))

    # 3. Moderation & Admin Commands
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("kick", kick_command))
    application.add_handler(CommandHandler("mute", mute_command))
    application.add_handler(CommandHandler("unmute", unmute_command))
    application.add_handler(CommandHandler("warn", warn_command))
    application.add_handler(CommandHandler("warns", warns_command))
    application.add_handler(CommandHandler("resetwarns", resetwarns_command))
    application.add_handler(CommandHandler("del", del_command))
    application.add_handler(CommandHandler("purge", purge_command))
    application.add_handler(CommandHandler("pin", pin_command))
    application.add_handler(CommandHandler("unpin", unpin_command))
    application.add_handler(CommandHandler("pinned", pinned_command))
    application.add_handler(CommandHandler("promote", promote_command))
    application.add_handler(CommandHandler("demote", demote_command))
    application.add_handler(CommandHandler("rules", rules_command))
    application.add_handler(CommandHandler("setrules", setrules_command))
    application.add_handler(CommandHandler("lock", lock_command))
    application.add_handler(CommandHandler("unlock", unlock_command))
    application.add_handler(CommandHandler("locks", locks_command))

    # 4. Interactive Group Settings
    application.add_handler(CommandHandler("settings", settings_command))

    # 5. Notes & Tags
    application.add_handler(CommandHandler("save", save_note_command))
    application.add_handler(CommandHandler("get", get_note_command))
    application.add_handler(CommandHandler("clear", clear_note_command))
    application.add_handler(CommandHandler("notes", list_notes_command))

    # 6. Fun & Utilities
    application.add_handler(CommandHandler("flirt", flirt_command))
    application.add_handler(CommandHandler("roast", roast_command))
    application.add_handler(CommandHandler("truth", truth_command))
    application.add_handler(CommandHandler("dare", dare_command))
    application.add_handler(CommandHandler("quote", quote_command))
    application.add_handler(CommandHandler("flip", flip_command))
    application.add_handler(CommandHandler("roll", roll_command))
    application.add_handler(CommandHandler("ship", ship_command))
    application.add_handler(CommandHandler("afk", afk_command))
    application.add_handler(CommandHandler(["info", "whois"], info_command))
    application.add_handler(CommandHandler("chatinfo", chatinfo_command))

    # 7. Callback Query Handlers (Inline Buttons)
    application.add_handler(CallbackQueryHandler(help_callback_handler, pattern=r"^help_"))
    application.add_handler(CallbackQueryHandler(settings_callback_handler, pattern=r"^set_"))

    # 8. Chat Member Event Handlers (Join/Leave/Bot Added)
    application.add_handler(ChatMemberHandler(on_chat_member_updated, ChatMemberHandler.MY_CHAT_MEMBER))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_new_members))
    application.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, on_left_member))

    # 9. Locks, AFK and Note Trigger Monitor (Group 1: runs first)
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, check_locks_and_afk), group=1)

    # 10. AI Chatbot Message Handler (Group 2: replies to mentions/replies/DMs)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_message_handler), group=2)

    # 11. Error Handler
    application.add_error_handler(error_handler)

    print(f"\n✨ {BOT_NAME} is active, beautiful and running! Press Ctrl+C to stop. 🌸💖\n")
    application.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
