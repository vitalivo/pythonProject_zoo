# bot.py

from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from handlers import start, handle_quiz

# Получите ваш токен здесь
TOKEN = '7792529237:AAHFAN5IHQykiURqlhQzcggsCOk9GeaPiaM'

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_quiz))
    app.run_polling()

