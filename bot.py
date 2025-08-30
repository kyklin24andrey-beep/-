import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Включим логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Определяем состояния для ConversationHandler
JOB_TITLE, COMPANY, LOCATION, SALARY, DESCRIPTION, LINK, CONFIRMATION = range(7)

# ID администраторов
ADMIN_IDS = [5665104217]

# Словарь для хранения временных данных о вакансиях
user_data = {}

# Список для хранения вакансий
vacancies = []

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def show_main_keyboard(update: Update, user_id):
    """Показывает основную клавиатуру"""
    if is_admin(user_id):
        keyboard = [['Добавить вакансию', 'Поиск вакансий']]
    else:
        keyboard = [['Поиск вакансий']]
        
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Выберите опцию:",
        reply_markup=reply_markup
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает разговор"""
    user = update.message.from_user
    logger.info("Пользователь %s начал разговор.", user.first_name)
    
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я бот для поиска работы."
    )
    await show_main_keyboard(update, user.id)
    return ConversationHandler.END

async def add_vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс добавления вакансии."""
    user = update.message.from_user
    
    if not is_admin(user.id):
        await update.message.reply_text("Только администраторы могут добавлять вакансии.")
        await show_main_keyboard(update, user.id)
        return ConversationHandler.END
        
    await update.message.reply_text(
        "Давайте добавим новую вакансию. Введите название должности:",
        reply_markup=ReplyKeyboardRemove()
    )
    return JOB_TITLE

async def job_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_data[user.id] = {'job_title': update.message.text}
    await update.message.reply_text("Отлично! Теперь введите название компании:")
    return COMPANY

async def company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_data[user.id]['company'] = update.message.text
    await update.message.reply_text("Теперь введите местоположение (город/страна):")
    return LOCATION

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_data[user.id]['location'] = update.message.text
    await update.message.reply_text("Введите зарплату или диапазон зарплат (необязательно):")
    return SALARY

async def salary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_data[user.id]['salary'] = update.message.text
    await update.message.reply_text("Теперь введите описание вакансии:")
    return DESCRIPTION

async def description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_data[user.id]['description'] = update.message.text
    await update.message.reply_text("Введите ссылку для отклика на вакансию:")
    return LINK

async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_data[user.id]['link'] = update.message.text
    
    vacancy_preview = (
        f"Проверьте введенные данные:\n\n"
        f"Должность: {user_data[user.id]['job_title']}\n"
        f"Компания: {user_data[user.id]['company']}\n"
        f"Местоположение: {user_data[user.id]['location']}\n"
        f"Зарплата: {user_data[user.id]['salary']}\n"
        f"Описание: {user_data[user.id]['description']}\n"
        f"Ссылка: {user_data[user.id]['link']}\n\n"
        f"Все верно? (да/нет)"
    )
    
    await update.message.reply_text(vacancy_preview)
    return CONFIRMATION

async def confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    response = update.message.text.lower()
    
    if response == 'да':
        new_vacancy = user_data[user.id].copy()
        vacancies.append(new_vacancy)
        await update.message.reply_text("✅ Вакансия успешно добавлена!")
    else:
        await update.message.reply_text("❌ Добавление вакансии отменено.")
    
    if user.id in user_data:
        del user_data[user.id]
    
    await show_main_keyboard(update, user.id)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if user.id in user_data:
        del user_data[user.id]
    await update.message.reply_text("Операция отменена.")
    await show_main_keyboard(update, user.id)
    return ConversationHandler.END

async def search_vacancies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not vacancies:
        await update.message.reply_text("📭 Пока нет доступных вакансий.")
        return await show_main_keyboard(update, update.message.from_user.id)
    
    keyboard = []
    for i, vacancy in enumerate(vacancies, 1):
        keyboard.append([f"📋 Вакансия {i}: {vacancy['job_title']}"])
    keyboard.append(['⬅️ Назад'])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите вакансию для просмотра:", reply_markup=reply_markup)

async def show_vacancy_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text.startswith("📋 Вакансия ") and ":" in text:
        try:
            vacancy_num = int(text.split(" ")[2].split(":")[0]) - 1
            if 0 <= vacancy_num < len(vacancies):
                vacancy = vacancies[vacancy_num]
                
                vacancy_details = (
                    f"🏢 **{vacancy['job_title']}**\n"
                    f"📋 **Компания:** {vacancy['company']}\n"
                    f"📍 **Местоположение:** {vacancy['location']}\n"
                    f"💰 **Зарплата:** {vacancy['salary']}\n"
                    f"📝 **Описание:** {vacancy['description']}\n\n"
                    f"🔗 **Ссылка для отклика:** {vacancy['link']}"
                )
                
                keyboard = [[InlineKeyboardButton("📨 Перейти к отклику", url=vacancy['link'])]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(vacancy_details, parse_mode='Markdown', reply_markup=reply_markup)
                await search_vacancies(update, context)  # Показываем список вакансий снова
                return
        except (ValueError, IndexError):
            pass
    
    await update.message.reply_text("Пожалуйста, выберите вакансию из списка.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user
    
    if text == 'Добавить вакансию':
        return await add_vacancy(update, context)
    elif text == 'Поиск вакансий':
        return await search_vacancies(update, context)
    elif text == '⬅️ Назад':
        return await start(update, context)
    elif text.startswith('📋 Вакансия '):
        return await show_vacancy_details(update, context)
    else:
        await update.message.reply_text("Используйте кнопки для навигации.")
        await show_main_keyboard(update, user.id)

def main():
    application = Application.builder().token("8479511135:AAEhD0qcdqumLLCugBRTETviDh2FDSY93mk").build()

    # ConversationHandler с ВСЕМИ состояниями
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^Добавить вакансию$'), add_vacancy),
            CommandHandler('add', add_vacancy)
        ],
        states={
            JOB_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, job_title)],
            COMPANY: [MessageHandler(filters.TEXT & ~filters.COMMAND, company)],
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, location)],
            SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, salary)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
            LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, link)],  # Важное состояние!
            CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmation)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CommandHandler("cancel", cancel))

    print("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()