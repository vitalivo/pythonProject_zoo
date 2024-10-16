#main.py

import os
import smtplib
from email.mime.text import MIMEText
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, ConversationHandler, filters, ApplicationBuilder, CallbackQueryHandler
from questions import questions
from animals import animal_scores

user_answers = {}

# Определяем этапы для обработки отзыва и контакта
FEEDBACK, WAITING_FOR_FEEDBACK = range(2)
WAITING_FOR_CONTACT = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    keyboard = [
        [InlineKeyboardButton("Начать викторину", callback_data="start_quiz")],
        [InlineKeyboardButton("Связаться с нами", callback_data="contact_us")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Уведомление о конфиденциальности
    privacy_notice = "Мы не собираем личные данные. Все ответы анонимны."
    await update.message.reply_text(privacy_notice)
    await update.message.reply_text('Привет! Это викторина "Тотемное животное". Нажмите, чтобы начать!', reply_markup=reply_markup)

async def handle_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка викторины"""
    query = update.callback_query
    await query.answer()

    if query.data == "start_quiz":
        user_answers[query.from_user.id] = []  # Инициализация списка ответов для пользователя
        await ask_question(query, 0)
    elif query.data == "care_program":
        await show_care_program(query)  # Показываем информацию о программе опеки
    elif query.data == "try_again":  # Новый обработчик для перезапуска
        await start(update, context)  # Запуск викторины заново
    elif query.data == "contact_us":  # Обработка команды "Связаться с нами"
        await contact_us(update, context)
    else:
        # Обработка ответа пользователя
        question_index = int(query.data.split("_")[1])
        answer = query.data.split("_")[2]
        user_answers[query.from_user.id].append(answer)  # Сохраняем ответ
        await ask_question(query, question_index + 1)

async def ask_question(query, question_index):
    """Задает вопрос пользователю"""
    if question_index < len(questions):
        question = questions[question_index]["question"]
        answers = questions[question_index]["answers"]
        keyboard = [[InlineKeyboardButton(answer, callback_data=f"answer_{question_index}_{answer}")] for answer in answers]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(question, reply_markup=reply_markup)
    else:
        # Подведение итогов
        await show_results(query)

async def show_results(query):
    """Показывает результаты викторины"""
    user_id = query.from_user.id
    answers = user_answers.get(user_id, [])

    if not answers:
        await query.edit_message_text("К сожалению, у вас нет ответов.")
        return

    animal_list = [animal_scores.get(answer, {"animal": "Неизвестно", "image": None}) for answer in answers]
    unique_animals = set(animal["animal"] for animal in animal_list)

    # Формируем сообщение с результатами
    result_message = "Ваши тотемные животные: " + ", ".join(unique_animals)
    result_message += "\n\nСпасибо за участие!"

    # Кнопка "Узнать больше"
    keyboard = [
        [InlineKeyboardButton("Узнать больше", callback_data="care_program")],
        [InlineKeyboardButton("Попробовать ещё раз", callback_data="start_quiz")],
        [InlineKeyboardButton("Поделиться в Facebook", url="https://www.facebook.com/sharer/sharer.php?u=YOUR_BOT_LINK"),
         InlineKeyboardButton("Поделиться в Twitter", url="https://twitter.com/intent/tweet?url=YOUR_BOT_LINK")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем результат
    await query.edit_message_text(result_message, reply_markup=reply_markup)

    # Отправляем изображения животных
    for animal in unique_animals:
        for data in animal_list:
            if data["animal"] == animal:
                if data["image"]:  # Проверяем наличие изображения
                    try:
                        await query.message.reply_photo(photo=open(data["image"], 'rb'), caption=data["animal"])
                    except FileNotFoundError:
                        await query.message.reply_text(f"Изображение для {data['animal']} недоступно.")
                else:
                    await query.message.reply_text(f"Изображение для {data['animal']} недоступно.")


async def show_care_program(query):
    """Показывает информацию о программе опеки"""
    care_info = (
        "Программа опеки позволяет вам поддерживать своих любимых животных!\n"
        "Вы можете стать опекуном животного, помогая обеспечивать его нужды.\n"
        "Узнайте больше на нашем сайте или свяжитесь с нашими сотрудниками."
    )
    await query.message.reply_text(care_info)

async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка команды /feedback"""
    await update.message.reply_text("Пожалуйста, оставьте ваш отзыв:")
    return WAITING_FOR_FEEDBACK  # Переход на следующий этап

async def receive_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение отзыва от пользователя"""
    user_feedback = update.message.text
    send_feedback_via_email(user_feedback)

    await update.message.reply_text("Ваш отзыв был отправлен, спасибо!")
    return ConversationHandler.END  # Завершение обработки

def send_feedback_via_email(feedback_text):
    try:
        msg = MIMEText(feedback_text)
        msg["Subject"] = "Отзыв пользователя"
        msg["From"] = os.getenv("EMAIL_USER")  # Используем переменную окружения
        msg["To"] = os.getenv("EMAIL_RECIPIENT")  # Используем переменную окружения

        with smtplib.SMTP("smtp.example.com", 587) as server:  # Замените на ваш SMTP-сервер
            server.starttls()
            server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASSWORD"))  # Ваши учетные данные
            server.send_message(msg)
    except Exception as e:
        print(f"Ошибка при отправке отзыва: {e}")

async def contact_us(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка команды /contact"""
    await update.message.reply_text("Пожалуйста, оставьте ваше сообщение:")
    return WAITING_FOR_CONTACT  # Переход на следующий этап

async def receive_contact_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение сообщения от пользователя для связи"""
    user_message = update.message.text
    send_contact_message_via_email(user_message)

    await update.message.reply_text("Ваше сообщение отправлено, спасибо!")
    return ConversationHandler.END  # Завершение обработки

def send_contact_message_via_email(contact_message):
    try:
        msg = MIMEText(contact_message)
        msg["Subject"] = "Сообщение от пользователя"
        msg["From"] = os.getenv("EMAIL_USER")  # Используем переменную окружения
        msg["To"] = os.getenv("EMAIL_RECIPIENT")  # Используем переменную окружения

        with smtplib.SMTP("smtp.example.com", 587) as server:  # Замените на ваш SMTP-сервер
            server.starttls()
            server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASSWORD"))  # Ваши учетные данные
            server.send_message(msg)
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")

# Настройка ConversationHandler для отзывов и контактов
feedback_handler = ConversationHandler(
    entry_points=[CommandHandler('feedback', feedback)],
    states={
        WAITING_FOR_FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_feedback)],
    },
    fallbacks=[]  # Здесь можно добавить обработчики на случай, если пользователь не хочет оставлять отзыв
)

contact_handler = ConversationHandler(
    entry_points=[CommandHandler('contact', contact_us)],
    states={
        WAITING_FOR_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_contact_message)],
    },
    fallbacks=[]  # Здесь можно добавить обработчики на случай, если пользователь не хочет оставлять сообщение
)

# Пример регистрации обработчиков в вашем основном файле
app = ApplicationBuilder().token("7792529237:AAHFAN5IHQykiURqlhQzcggsCOk9GeaPiaM").build

