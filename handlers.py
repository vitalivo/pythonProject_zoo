from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters
from questions import questions
from animals import animal_scores
import logging

user_answers = {}

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Определяем этапы для обработки отзыва
FEEDBACK, WAITING_FOR_CONTACT = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    keyboard = [
        [InlineKeyboardButton("Начать викторину", callback_data="start_quiz")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
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
    elif query.data == "contact_staff":
        await contact_staff(query)  # Контакт с сотрудником
    elif query.data == "restart_quiz":
        await start(update, context)  # Перезапуск викторины
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

    # Получаем список животных по ответам
    animal_list = [animal_scores.get(answer, {"animal": "Животное не определено", "image": None}) for answer in answers]
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
        if animal != "Животное не найдено":  # Пропускаем неопределенных животных
            for data in animal_list:
                if data["animal"] == animal and data["image"]:  # Проверяем наличие изображения
                    try:
                        await query.message.reply_photo(photo=open(data["image"], 'rb'), caption=data["animal"])
                    except FileNotFoundError:
                        await query.message.reply_text(f"Изображение для {data['animal']} недоступно.")


# async def show_results(query):
#     """Показывает результаты викторины"""
#     user_id = query.from_user.id
#     answers = user_answers.get(user_id, [])
#
#     if not answers:
#         await query.edit_message_text("К сожалению, у вас нет ответов.")
#         return
#
#     animal_list = [animal_scores.get(answer, {"animal": "Неизвестно"}) for answer in answers]
#     unique_animals = set(animal["animal"] for animal in animal_list)
#
#     # Формируем сообщение с результатами
#     result_message = "Ваши тотемные животные: " + ", ".join(unique_animals)
#     result_message += "\n\nСпасибо за участие!"
#
#     # Кнопки для дележа в соцсетях
#     keyboard = [
#         [InlineKeyboardButton("Узнать больше", callback_data="care_program")],
#         [InlineKeyboardButton("Попробовать еще раз", callback_data="start_quiz")],
#         [
#             InlineKeyboardButton("Поделиться в Facebook", url="https://www.facebook.com/sharer/sharer.php?u=YOUR_BOT_LINK"),
#             InlineKeyboardButton("Поделиться в Twitter", url="https://twitter.com/intent/tweet?url=YOUR_BOT_LINK")
#         ]
#     ]
#
#     # Отправляем результат
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     await query.edit_message_text(result_message, reply_markup=reply_markup)
#
#     # Отправляем изображения животных
#     for animal in unique_animals:
#         for data in animal_list:
#             if data["animal"] == animal:
#                 await query.message.reply_photo(photo=open(data["image"], 'rb'), caption=data["animal"])


async def show_care_program(query):
    """Показывает информацию о программе опеки"""
    care_info = (
        "Программа опеки позволяет вам поддерживать своих любимых животных!\n"
        "Вы можете стать опекуном животного, помогая обеспечивать его нужды.\n"
        "Узнайте больше на нашем сайте или свяжитесь с нашими сотрудниками."
    )
    await query.message.reply_text(care_info)


async def contact_staff(query):
    """Контакт с сотрудником"""
    await query.message.reply_text("Вы можете связаться с нами по почте: contact@zoo.com")


async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка команды /feedback"""
    await update.message.reply_text("Пожалуйста, оставьте ваш отзыв:")
    return FEEDBACK  # Переход на следующий этап


async def receive_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение отзыва от пользователя"""
    user_feedback = update.message.text
    # Здесь вы можете добавить код для отправки отзыва по электронной почте
    await update.message.reply_text("Ваш отзыв был отправлен, спасибо!")
    return ConversationHandler.END  # Завершение обработки


# Определяем обработчики
feedback_handler = ConversationHandler(
    entry_points=[CommandHandler("feedback", feedback)],
    states={
        FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_feedback)],
    },
    fallbacks=[],
)

# Не забудьте добавить обработчики в ваш основной код бота





