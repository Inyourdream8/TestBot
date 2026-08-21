import logging
import os
import sys
import json
import time
import asyncio
from datetime import datetime
import httpx
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
import gspread

# ---------------- Structured Logging Setup ----------------
class JSONFormatter(logging.Formatter):
    """Outputs logs in JSON format for production analysis."""
    def format(self, record):
        log_object = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_object)

logger = logging.getLogger("telegram_bot")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")

# ---------------- Google Sheets Setup ----------------
def _get_sheet_sync():
    client = gspread.service_account(filename="service.json")
    return client.open("Daily Life Bot Data").sheet1

def _append_row_sync(row_data):
    sheet = _get_sheet_sync()
    sheet.append_row(row_data)

async def append_row_async(row_data):
    await asyncio.to_thread(_append_row_sync, row_data)

async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.message.reply_text("ប្រើ: /addexpense <ចំនួន> <ប្រភេទ>")
        return
    amount = context.args[0]
    category = " ".join(context.args[1:])
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    try:
        await append_row_async([date_str, category, amount])
        await update.message.reply_text(f"បានកត់ចំណាយ: {amount} សម្រាប់ {category}")
    except Exception as e:
        logger.error(f"Sheets error: {e}")
        await update.message.reply_text("⚠️ បរាជ័យក្នុងការកត់ត្រាទៅក្នុង Google Sheet")

async def add_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("ប្រើ: /addnote <អត្ថបទកំណត់ចំណាំ>")
        return
    note_text = " ".join(context.args)
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    try:
        await append_row_async([date_str, "Note", note_text])
        await update.message.reply_text(f"បានកត់កំណត់ចំណាំ: {note_text}")
    except Exception as e:
        logger.error(f"Sheets error: {e}")
        await update.message.reply_text("⚠️ បរាជ័យក្នុងការកត់ត្រាទៅក្នុង Google Sheet")

async def add_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("ប្រើ: /addreminder <ការរំលឹក>")
        return
    reminder_text = " ".join(context.args)
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    try:
        await append_row_async([date_str, "Reminder", reminder_text])
        await update.message.reply_text(f"បានកំណត់ការរំលឹក: {reminder_text}")
    except Exception as e:
        logger.error(f"Sheets error: {e}")
        await update.message.reply_text("⚠️ បរាជ័យក្នុងការកត់ត្រាទៅក្នុង Google Sheet")

# ---------------- Google Search Setup ----------------
async def google_search(query: str) -> dict:
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"q": query, "key": GOOGLE_API_KEY, "cx": GOOGLE_CX}
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        return response.json()

# ---------------- Ollama Streaming Integration ----------------
async def stream_ollama_response(update: Update, prompt: str) -> None:
    """Streams completion from local Ollama instance and updates Telegram message."""
    placeholder_msg = await update.message.reply_text("Thinking... 🤖")
    
    payload = {
        "model": "qwen3.5:9b",
        "prompt": prompt,
        "stream": True
    }
    
    full_response = ""
    last_update_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", "http://localhost:11434/api/generate", json=payload) as response:
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    full_response += chunk.get("response", "")
                    
                    # Rate limit message edits to once every 1.5 seconds to comply with Telegram Limits
                    if time.time() - last_update_time > 1.5 and full_response.strip():
                        try:
                            await placeholder_msg.edit_text(full_response + " ▌")
                            last_update_time = time.time()
                        except Exception:
                            pass  # Ignore rate-limit or identical content edit errors
                            
                # Final edit without typing cursor
                if full_response.strip():
                    await placeholder_msg.edit_text(full_response)
                else:
                    await placeholder_msg.edit_text("⚠️ Received empty response from AI model.")

    except Exception as e:
        logger.error(f"Ollama streaming failure: {e}")
        await placeholder_msg.edit_text("⚠️ Could not connect to AI service.")

# ---------------- Navigation & Message Handlers ----------------
async def post_init(application) -> None:
    commands = [
        BotCommand("start", "Start the bot and view main menu"),
        BotCommand("help", "Show help information"),
        BotCommand("addexpense", "Add expense to Google Sheet"),
        BotCommand("addnote", "Add note to Google Sheet"),
        BotCommand("addreminder", "Add reminder to Google Sheet"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Persistent menu commands initialized.")

def get_main_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("About", callback_data="about"),
            InlineKeyboardButton("Who is it for?", callback_data="who_for"),
        ],
        [InlineKeyboardButton("Contact", callback_data="contact")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reply_keyboard = [[KeyboardButton("Start Menu 🚀"), KeyboardButton("Help ℹ️")]]
    reply_markup_persistent = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    welcome_text = "Welcome to the Telegram Bot! 🚀\n\nPlease choose an option below or use the menu commands to navigate."
    
    if update.message:
        await update.message.reply_text("Bottom menu keyboard activated.", reply_markup=reply_markup_persistent)
        await update.message.reply_text(welcome_text, reply_markup=get_main_inline_keyboard())
    elif update.callback_query:
        await update.callback_query.message.reply_text(welcome_text, reply_markup=get_main_inline_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "Here are the available commands:\n"
        "/start - Welcome message and interactive menu\n"
        "/help - Show this help information\n"
        "/addexpense <ចំនួន> <ប្រភេទ> - កត់ចំណាយទៅក្នុង Google Sheet\n"
        "/addnote <អត្ថបទកំណត់ចំណាំ> - កត់កំណត់ចំណាំទៅក្នុង Google Sheet\n"
        "/addreminder <ការរំលឹក> - កំណត់ការរំលឹកទៅក្នុង Google Sheet\n\n"
        "💡 Tip: Just type a normal sentence like 'I want you to research AI news' and the bot will search automatically."
    )
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()

    if text == "Start Menu 🚀":
        await start(update, context)
        return
    elif text == "Help ℹ️":
        await help_command(update, context)
        return

    if "research" in text.lower() or "search" in text.lower():
        try:
            results = await google_search(text)
            if "items" in results:
                reply = "\n\n".join([f"{item['title']}\n{item['link']}" for item in results["items"][:3]])
            else:
                reply = "⚠️ No search results found."
            await update.message.reply_text(reply)
        except Exception as e:
            logger.error(f"Search error: {e}")
            await update.message.reply_text("⚠️ Search service unavailable.")
        return

    # Trigger streaming response for general AI queries
    await stream_ollama_response(update, text)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "back_to_menu":
        welcome_text = "Welcome to the Telegram Bot! 🚀\n\nPlease choose an option below or use the menu commands to navigate."
        await query.edit_message_text(text=welcome_text, reply_markup=get_main_inline_keyboard())
        return

    if data == "about":
        text = (
            "ℹ️ *About This Bot*\n\n"
            "This bot integrates Google Sheets logging, AI responses, and web search.\n"
            "It demonstrates command handling, persistent menus, and interactive inline keyboards."
        )
    elif data == "who_for":
        text = (
            "🎯 *Who is it for?*\n\n"
            "It is for developers who want a boilerplate Telegram bot with Google Sheets + AI + search integration."
        )
    elif data == "contact":
        text = (
            "📧 *Contact*\n\n"
            "Feel free to check out the repository or reach out if you have any questions."
        )
    else:
        text = "Unknown option selected."

    keyboard = [[InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="Markdown")

def main() -> None:
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("TELEGRAM_BOT_TOKEN is missing or not configured!")
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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))

    logger.info("Starting bot polling system...")
    application.run_polling()

if __name__ == "__main__":
    main()