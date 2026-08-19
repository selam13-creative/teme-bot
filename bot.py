import os
import threading
import logging

from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Simple /start handler."""
    await update.message.reply_text("Hello! I'm running. Send /health to check the web server.")

async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Telegram-side health check."""
    await update.message.reply_text("OK")

# Build the Telegram bot application if we have a token
application = None
if TELEGRAM_TOKEN:
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("health", health_command))
else:
    logger.warning("TELEGRAM_TOKEN not set; Telegram bot will not start.")


def run_bot() -> None:
    """Run the Telegram bot polling loop. This will block, so we run it in a thread."""
    if application is None:
        logger.info("No application to run (missing TELEGRAM_TOKEN). Skipping bot start.")
        return

    logger.info("Starting Telegram bot polling in background thread...")
    # run_polling manages its own asyncio loop and will block until stopped
    application.run_polling()


# ---- Simple Flask app for Render (or any host that exposes PORT) ----
flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return "OK - bot is running\n"

@flask_app.route("/health")
def health():
    return "OK"


# Start the bot in a daemon thread so the Flask web server can run in the main thread
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    # Listen on all interfaces for Render; Flask's dev server is fine for a simple liveness endpoint.
    logger.info(f"Starting Flask server on 0.0.0.0:{port}")
    flask_app.run(host="0.0.0.0", port=port)
