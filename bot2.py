import logging
import os
import aiohttp  # Use aiohttp for async HTTP requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ContextTypes,
    CallbackQueryHandler, MessageHandler, filters
)

# Set your Telegram Bot Token directly or via Railway environment variable
API_KEY = os.getenv("API_KEY")  # Set this in Railway's "Variables" tab

# Logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Currency conversion base URL
CONVERSION_URL = 'https://api.exchangerate-api.com/v4/latest/INR'

# Store user's conversion choice
user_conversion_choice = {}

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Convert USD to INR", callback_data='USD_INR')],
        [InlineKeyboardButton("Convert INR to USD", callback_data='INR_USD')],
        [InlineKeyboardButton("Convert USD to EUR", callback_data='USD_EUR')],
        [InlineKeyboardButton("Convert EUR to USD", callback_data='EUR_USD')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome! Choose a conversion option:", reply_markup=reply_markup)

# Handle button click
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_conversion_choice[query.from_user.id] = query.data
    await query.edit_message_text("Please enter the amount you want to convert:")

# Handle amount input
async def handle_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id not in user_conversion_choice:
        await update.message.reply_text("Please use /start to select a conversion option first.")
        return
    try:
        amount = float(update.message.text)
        conversion_choice = user_conversion_choice[user_id]
        conversion_rate = await get_conversion_rate(conversion_choice)

        if conversion_rate is None:
            await update.message.reply_text("Sorry, I couldn't fetch the conversion rate.")
            return

        result = amount * conversion_rate
        await update.message.reply_text(f"The conversion result is: {result:.2f}")
        await show_conversion_buttons(update)

    except ValueError:
        await update.message.reply_text("Please enter a valid number.")

    del user_conversion_choice[user_id]

# Fetch conversion rate
async def get_conversion_rate(conversion_choice: str) -> float:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(CONVERSION_URL) as response:
                data = await response.json()
                if conversion_choice == 'USD_INR':
                    return data['rates']['INR'] / data['rates']['USD']
                elif conversion_choice == 'INR_USD':
                    return data['rates']['USD'] / data['rates']['INR']
                elif conversion_choice == 'USD_EUR':
                    return data['rates']['EUR'] / data['rates']['USD']
                elif conversion_choice == 'EUR_USD':
                    return data['rates']['USD'] / data['rates']['EUR']
                return None
    except aiohttp.ClientError as e:
        logger.error(f"Error fetching conversion rates: {e}")
        return None

# Show conversion buttons again
async def show_conversion_buttons(update: Update) -> None:
    keyboard = [
        [InlineKeyboardButton("Convert USD to INR", callback_data='USD_INR')],
        [InlineKeyboardButton("Convert INR to USD", callback_data='INR_USD')],
        [InlineKeyboardButton("Convert USD to EUR", callback_data='USD_EUR')],
        [InlineKeyboardButton("Convert EUR to USD", callback_data='EUR_USD')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose another conversion option:", reply_markup=reply_markup)

# Entry point
def main() -> None:
    application = Application.builder().token(API_KEY).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount_input))

    # Run using polling (no webhook)
    application.run_polling()

if __name__ == "__main__":
    main()
