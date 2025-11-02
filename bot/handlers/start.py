from telegram import Update
from telegram.ext import CallbackContext
from bot.database import Database
from bot.keyboards import get_main_menu

db = Database()

async def start_handler(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    
    existing_user = db.get_user_by_id(user_id)
    
    if existing_user:
        await update.message.reply_text(
            f"С возвращением, {user.first_name}!\n"
            "Используйте меню для работы с ботом.",
            reply_markup=get_main_menu()
        )
    else:
        await update.message.reply_text(
            "Добро пожаловать! Для регистрации введите ключ доступа:"
        )
        context.user_data['awaiting_key'] = True

async def help_handler(update: Update, context: CallbackContext):
    help_text = """
🤖 Бот для расчета заработка сотрудников

Основные функции:
📅 - Управление сменами
💰 - Расчет заработка за смену
📊 - Отчет за текущий месяц

Для начала работы зарегистрируйтесь с помощью ключа.
    """
    await update.message.reply_text(help_text)