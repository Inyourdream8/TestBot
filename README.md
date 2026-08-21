# Python TelegramBot Template

This repository contains a clean, modern template for a Telegrambot using the `python-telegram-bot` library (v20+ with asynchronous support).

## Features

- **Persistent Menu Button**: A bottom-left menu containing `/start` and `/help` commands configured automatically in the client.
- **Inline Keyboard Buttons**: Interactive buttons ("About", "Who is it for?", "Contact") below message text.
- **Interactive Callbacks**: Handlers that capture button clicks and dynamically update the message text with back navigation support.
- **Secure Token Management**: Utilizes environment variables (`.env` file) to store sensitive API credentials safely.

---

## Getting Started

### 1. Prerequisites

Ensure you have **Python 3.8 or higher** installed.

### 2. Set Up a Virtual Environment (Optional but Recommended)

In your terminal, navigate to the project directory and run:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

Install the required packages from the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### 4. Obtain a Bot Token

1. Open Telegram and search for `@BotFather`.
2. Send the `/newbot` command and follow the instructions to choose a name and username.
3. Copy the API Token provided.

### 5. Configure Environment Variables

Create a file named `.env` in the root of the project (copying `.env.example` as a template):

```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` in a text editor and replace `YOUR_BOT_TOKEN_HERE` with your actual Telegram bot token:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
```

### 6. Run the Bot

Start the bot application by running:

```bash
python main.py
```

You should see logs outputting to the console:

```text
INFO - telegram.ext.Application - Application started
INFO - __main__ - Persistent menu commands set successfully.
INFO - __main__ - Starting bot polling...
```

To stop the bot, press `Ctrl + C` in the terminal.

---

## File Structure

```text
TelegramBot/
├── .env.example          # Environment variables template
├── requirements.txt      # Python dependencies
├── main.py               # Main bot application entrypoint
└── README.md             # This instructions file
```
