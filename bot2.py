import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
import requests
import os

# Replace with your actual API key for Telegram Bot
API_KEY = os.getenv("API_KEY")

# Set up logging to get feedback in the terminal
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversion rate API for currency conversion
CONVERSION_URL = 'https://api.exchangerate-api.com/v4/latest/INR'  # Replace with the base currency you prefer

# Store the user's conversion choice temporarily
user_conversion_choice = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message and show buttons."""
    keyboard = [
        [InlineKeyboardButton("Convert USD to INR", callback_data='USD_INR')],
        [InlineKeyboardButton("Convert INR to USD", callback_data='INR_USD')],
        [InlineKeyboardButton("Convert USD to EUR", callback_data='USD_EUR')],
        [InlineKeyboardButton("Convert EUR to USD", callback_data='EUR_USD')],
        # Add more buttons as needed
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome! Choose a conversion option:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses and prompt the user for an amount."""
    query = update.callback_query
    await query.answer()  # Acknowledge the button press

    # Store the user's conversion choice
    user_conversion_choice[query.from_user.id] = query.data

    # Ask the user for the amount to convert
    await query.edit_message_text("Please enter the amount you want to convert:")

# Function to handle user's amount input
async def handle_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user's input for the amount to convert."""
    user_id = update.message.from_user.id
    if user_id not in user_conversion_choice:
        await update.message.reply_text("Please use /start to select a conversion option first.")
        return
    
    try:
        # Get the amount the user entered
        amount = float(update.message.text)
        conversion_choice = user_conversion_choice[user_id]

        # Perform the conversion based on the user's choice
        conversion_rate = await get_conversion_rate(conversion_choice)
        if conversion_rate is None:
            await update.message.reply_text("Sorry, I couldn't fetch the conversion rate. Please try again later.")
            return
        
        result = amount * conversion_rate
        # Send the conversion result
        await update.message.reply_text(f"The conversion result is: {result:.2f}")
        
        # After conversion, show the conversion buttons again
        await show_conversion_buttons(update)

    except ValueError:
        await update.message.reply_text("Please enter a valid number.")

    # Clear the user's conversion choice after the conversion
    del user_conversion_choice[user_id]

async def get_conversion_rate(conversion_choice: str) -> float:
    """Get conversion rate from an API."""
    response = requests.get(CONVERSION_URL)
    data = response.json()

    # Define the conversion pairs and rates
    if conversion_choice == 'USD_INR':
        return data['rates']['INR'] / data['rates']['USD']
    elif conversion_choice == 'INR_USD':
        return data['rates']['USD'] / data['rates']['INR']
    elif conversion_choice == 'USD_EUR':
        return data['rates']['EUR'] / data['rates']['USD']
    elif conversion_choice == 'EUR_USD':
        return data['rates']['USD'] / data['rates']['EUR']
    return None

async def show_conversion_buttons(update: Update) -> None:
    """Show the conversion buttons again after a conversion."""
    keyboard = [
        [InlineKeyboardButton("Convert USD to INR", callback_data='USD_INR')],
        [InlineKeyboardButton("Convert INR to USD", callback_data='INR_USD')],
        [InlineKeyboardButton("Convert USD to EUR", callback_data='USD_EUR')],
        [InlineKeyboardButton("Convert EUR to USD", callback_data='EUR_USD')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose another conversion option:", reply_markup=reply_markup)

def main() -> None:
    """Start the bot."""
    # Set up the application and handlers
    application = Application.builder().token(API_KEY).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount_input))

    # Run the bot until it is stopped
    application.run_polling()

# Ensure this runs only when the script is executed
if __name__ == "__main__":
    main()  # Start the bot
