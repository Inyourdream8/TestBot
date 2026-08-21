import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# Google Sheets imports
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Retrieve Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ---------------- Google Sheets Setup ----------------
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("service.json", scope)
    client = gspread.authorize(creds)
    return client.open("Daily Life Bot Data").sheet1

async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sheet = get_sheet()
    if len(context.args) < 2:
        await update.message.reply_text("ប្រើ: /addexpense <ចំនួន> <ប្រភេទ>")
        return
    amount = context.args[0]
    category = " ".join(context.args[1:])
    sheet.append_row(["2026-07-20", category, amount])
    await update.message.reply_text(f"បានកត់ចំណាយ: {amount} សម្រាប់ {category}")

async def add_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sheet = get_sheet()
    if not context.args:
        await update.message.reply_text("ប្រើ: /addnote <អត្ថបទកំណត់ចំណាំ>")
        return
    note_text = " ".join(context.args)
    date_str = datetime.now().strftime("%Y-%m-%d")
    sheet.append_row([date_str, "Note", note_text])
    await update.message.reply_text(f"បានកត់កំណត់ចំណាំ: {note_text}")

async def add_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sheet = get_sheet()
    if not context.args:
        await update.message.reply_text("ប្រើ: /addreminder <ការរំលឹក>")
        return
    reminder_text = " ".join(context.args)
    date_str = datetime.now().strftime("%Y-%m-%d")
    sheet.append_row([date_str, "Reminder", reminder_text])
    await update.message.reply_text(f"បានកំណត់ការរំលឹក: {reminder_text}")
# -----------------------------------------------------

async def post_init(application) -> None:
    commands = [
        BotCommand("start", "Start the bot and view main menu"),
        BotCommand("help", "Show help information"),
        BotCommand("addexpense", "Add expense to Google Sheet"),
        BotCommand("addnote", "Add note to Google Sheet"),
        BotCommand("addreminder", "Add reminder to Google Sheet"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Persistent menu commands set successfully.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reply_keyboard = [
        [KeyboardButton("Start Menu 🚀"), KeyboardButton("Help ℹ️")]
    ]
    reply_markup_persistent = ReplyKeyboardMarkup(
        reply_keyboard, resize_keyboard=True
    )
    
    inline_keyboard = [
        [
            InlineKeyboardButton("About", callback_data="about"),
            InlineKeyboardButton("Who is it for?", callback_data="who_for"),
        ],
        [InlineKeyboardButton("Contact", callback_data="contact")],
    ]
    inline_markup = InlineKeyboardMarkup(inline_keyboard)
    
    welcome_text = (
        "Welcome to the Telegram Bot! 🚀\n\n"
        "Please choose an option below or use the menu commands to navigate."
    )
    
    if update.message:
        await update.message.reply_text(
            "Bottom menu keyboard activated.",
            reply_markup=reply_markup_persistent,
        )
        await update.message.reply_text(welcome_text, reply_markup=inline_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(welcome_text, reply_markup=inline_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "Here are the available commands:\n"
        "/start - Welcome message and interactive menu\n"
        "/help - Show this help information\n"
        "/addexpense <ចំនួន> <ប្រភេទ> - កត់ចំណាយទៅក្នុង Google Sheet\n"
        "/addnote <អត្ថបទកំណត់ចំណាំ> - កត់កំណត់ចំណាំទៅក្នុង Google Sheet\n"
        "/addreminder <ការរំលឹក> - កំណត់ការរំលឹកទៅក្នុង Google Sheet\n\n"
        "You can also use the Menu button in the bottom-left to access these commands anytime."
    )
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    if text == "Start Menu 🚀":
        await start(update, context)
    elif text == "Help ℹ️":
        await help_command(update, context)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "about":
        text = (
            "ℹ️ **About This Bot**\n\n"
            "This is a template TelegramBot built using the `python-telegram-bot` library.\n"
            "It demonstrates command handling, persistent menus, and interactive inline keyboards."
        )
    elif data == "who_for":
        text = (
            "🎯 **Who is it for?**\n\n"
            "It is for Python developers looking for a boilerplate starting point "
            "to build rich, interactive Telegram bots with clean and structured code."
        )
    elif data == "contact":
        text = (
            "📧 **Contact**\n\n"
            "Feel free to check out the repository or reach out if you have any questions."
        )
    elif data == "back_to_menu":
        keyboard = [
            [
                InlineKeyboardButton("About", callback_data="about"),
                InlineKeyboardButton("Who is it for?", callback_data="who_for"),
            ],
            [InlineKeyboardButton("Contact", callback_data="contact")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=(
                "Welcome to the Telegram Bot! 🚀\n\n"
                "Please choose an option below or use the menu commands to navigate."
            ),
            reply_markup=reply_markup,
        )
        return
    else:
        text = "Unknown option selected."

    keyboard = [[InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=text, reply_markup=reply_markup, parse_mode="Markdown"
    )

def main() -> None:
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error(
            "TELEGRAM_BOT_TOKEN is missing or not configured!\n"
            "Please create a '.env' file based on '.env.example' and insert your Telegram bot token."
        )
        sys.exit(1)

    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("addexpense", add_expense))
    application.add_handler(CommandHandler("addnote", add_note))
    application.add_handler(CommandHandler("addreminder", add_reminder))

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    application.add_handler(CallbackQueryHandler(button_callback))

    logger.info("Starting bot polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
