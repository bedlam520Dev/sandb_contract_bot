"""
Telegram Bot for Monitoring Solana and Sui Network Transactions.

This bot tracks blockchain transactions for Solana and Sui using Firebase
for persistent storage and Replit for hosting.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters
import logging
import firebase_admin
from firebase_admin import credentials, db
import os
from keep_alive import keep_alive
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Firebase Admin
cred = credentials.Certificate("firebase_credentials.json")  # Add your Firebase JSON file
firebase_admin.initialize_app(cred, {"databaseURL": os.getenv("FIREBASE_URL")})
ref = db.reference("/users")

# Command handlers
def start(update: Update, context: CallbackContext) -> None:
    """Handles the /start command."""
    update.message.reply_text(
        "Welcome to the Blockchain Tracker Bot! Use /track to monitor transactions. "
        "Use /help for other commands."
    )

def help_command(update: Update, context: CallbackContext) -> None:
    """Handles the /help command."""
    update.message.reply_text(
        "/start - Start the bot\n"
        "/track - Start tracking a contract address\n"
        "/status - View tracked addresses\n"
        "/stop - Stop tracking a contract\n"
        "/help - Show help message"
    )

def track(update: Update, context: CallbackContext) -> None:
    """Handles the /track command and initiates tracking."""
    keyboard = [
        [InlineKeyboardButton("Solana", callback_data="solana"),
         InlineKeyboardButton("Sui", callback_data="sui")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "Which network would you like to track?", reply_markup=reply_markup
    )

def handle_network_selection(update: Update, context: CallbackContext) -> None:
    """Handles network selection via button."""
    query = update.callback_query
    query.answer()
    network = query.data
    context.user_data['network'] = network
    query.edit_message_text(
        text=f"You selected {network.capitalize()}. Please send the contract address you want to track."
    )

def handle_contract_address(update: Update, context: CallbackContext) -> None:
    """Handles the input of a contract address."""
    contract_address = update.message.text
    network = context.user_data.get('network')

    if not network:
        update.message.reply_text("Please select a network first using /track.")
        return

    user_id = update.effective_user.id
    user_data = ref.child(str(user_id)).get() or {}
    user_data.setdefault(network, []).append(contract_address)
    ref.child(str(user_id)).set(user_data)

    update.message.reply_text(
        f"Started tracking contract address: {contract_address} on {network.capitalize()}."
    )

def status(update: Update, context: CallbackContext) -> None:
    """Handles the /status command."""
    user_id = update.effective_user.id
    user_data = ref.child(str(user_id)).get()

    if not user_data:
        update.message.reply_text("You are not tracking any contracts.")
        return

    message = "Currently tracked contracts:\n"
    for network, contracts in user_data.items():
        message += f"\n{network.capitalize()}:\n"
        message += "\n".join(contracts) + "\n"

    update.message.reply_text(message)

def stop(update: Update, context: CallbackContext) -> None:
    """Handles the /stop command to stop tracking."""
    user_id = update.effective_user.id
    ref.child(str(user_id)).delete()
    update.message.reply_text("Stopped tracking all contracts.")

def main() -> None:
    """Main function to start the bot."""
    updater = Updater(os.getenv("TELEGRAM_TOKEN"))
    dispatcher = updater.dispatcher

    # Command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("track", track))
    dispatcher.add_handler(CommandHandler("status", status))
    dispatcher.add_handler(CommandHandler("stop", stop))

    # Callback query handler for buttons
    dispatcher.add_handler(CallbackQueryHandler(handle_network_selection))

    # Message handler for contract address input
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_contract_address))

if __name__ == "__main__":
    keep_alive()
    main()

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
