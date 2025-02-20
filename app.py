from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler, MessageHandler, filters
from credentials import BOT_TOKEN, BOT_USERNAME
import json

async def launch_web_ui(update: Update, callback: CallbackContext):
    kb = [
        [KeyboardButton("TAP TO EARN!!!", web_app=WebAppInfo("https://v0-pesa-swap-52-f2lgcm.vercel.app/"))]
    ]
    await update.message.reply_text("Enjoy Tapping ... ", reply_markup=ReplyKeyboardMarkup(kb))


if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler('start', launch_web_ui))

    print(f"Your bot is listening! Navigate to http://t.me/{BOT_USERNAME} to interact with it!")
    application.run_polling()