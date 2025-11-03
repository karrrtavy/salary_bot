import logging
import os
import sys
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext
from telegram import Update

from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram import Update

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.config import BOT_TOKEN
from bot.database import Database
from bot.handlers.start import start_handler, help_handler
from bot.handlers.registration import handle_registration_key, handle_hourly_rate, handle_percent
from bot.handlers.shifts import shifts_handler, add_shift_handler, handle_shift_date, delete_shift_handler, handle_shift_delete, show_shifts_handler
from bot.handlers.salary import salary_handler, handle_hours_input, handle_start_revenue, handle_end_revenue, confirm_salary_handler, payment_history_handler, custom_period_handler, handle_period_input, payment_history_handler, handle_shift_selection

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def log_command(user, command, response="OK"):
    """Логирование команд пользователя"""
    logger.info(f"USER: {user.id} ({user.first_name} @{user.username}) | COMMAND: {command} | RESPONSE: {response}")

class SalaryBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.db = Database()
        self.setup_handlers()

    def setup_handlers(self):
        # Команды
        self.application.add_handler(CommandHandler("start", self.wrapped_start_handler))
        self.application.add_handler(CommandHandler("help", self.wrapped_help_handler))
        
        # Обработчики меню
        self.application.add_handler(MessageHandler(filters.Text(["❓ Помощь"]), self.wrapped_help_handler))
        self.application.add_handler(MessageHandler(filters.Text(["📅 Мои смены"]), self.wrapped_shifts_handler))
        self.application.add_handler(MessageHandler(filters.Text(["➕ Добавить смену"]), self.wrapped_add_shift_handler))
        self.application.add_handler(MessageHandler(filters.Text(["➖ Удалить смену"]), self.wrapped_delete_shift_handler))
        self.application.add_handler(MessageHandler(filters.Text(["📋 Мои смены"]), self.wrapped_show_shifts_handler))
        self.application.add_handler(MessageHandler(filters.Text(["🔙 Назад"]), self.wrapped_start_handler))
        self.application.add_handler(MessageHandler(filters.Text(["💰 Расчет зарплаты"]), self.wrapped_salary_handler))
        
        # Новые обработчики выбора смены
        self.application.add_handler(MessageHandler(filters.Text(["📅 Смена за сегодня"]), self.wrapped_shift_selection))
        self.application.add_handler(MessageHandler(filters.Regex(r'^📋 \d{2}\.\d{2}\.\d{4}$'), self.wrapped_shift_selection))
        
        # Новые обработчики периодов
        self.application.add_handler(MessageHandler(filters.Text(["📊 Расчет за период"]), self.wrapped_custom_period_handler))
        self.application.add_handler(MessageHandler(filters.Text(["📜 История выплат"]), self.wrapped_payment_history_handler))
        
        self.application.add_handler(MessageHandler(filters.Text(["✅ Подтвердить"]), self.wrapped_confirm_salary_handler))
        self.application.add_handler(MessageHandler(filters.Text(["✏️ Изменить"]), self.wrapped_salary_handler))
        self.application.add_handler(MessageHandler(filters.Text(["❌ Отмена"]), self.wrapped_start_handler))
        
        # Динамические обработчики
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handle_dynamic_input
        ))

    # Обертки для логирования
    async def wrapped_start_handler(self, update: Update, context: CallbackContext):
        await start_handler(update, context)
        log_command(update.effective_user, "start")

    async def wrapped_help_handler(self, update: Update, context: CallbackContext):
        await help_handler(update, context)
        log_command(update.effective_user, "help")

    async def wrapped_shifts_handler(self, update: Update, context: CallbackContext):
        await shifts_handler(update, context)
        log_command(update.effective_user, "shifts_menu")

    async def wrapped_add_shift_handler(self, update: Update, context: CallbackContext):
        await add_shift_handler(update, context)
        log_command(update.effective_user, "add_shift")

    async def wrapped_delete_shift_handler(self, update: Update, context: CallbackContext):
        await delete_shift_handler(update, context)
        log_command(update.effective_user, "delete_shift")

    async def wrapped_show_shifts_handler(self, update: Update, context: CallbackContext):
        await show_shifts_handler(update, context)
        log_command(update.effective_user, "show_shifts")

    async def wrapped_salary_handler(self, update: Update, context: CallbackContext):
        await salary_handler(update, context)
        log_command(update.effective_user, "salary_calculation")

    async def wrapped_shift_selection(self, update: Update, context: CallbackContext):
        await handle_shift_selection(update, context)
        log_command(update.effective_user, "shift_selection")

    async def wrapped_custom_period_handler(self, update: Update, context: CallbackContext):
        await custom_period_handler(update, context)
        log_command(update.effective_user, "custom_period")

    async def wrapped_payment_history_handler(self, update: Update, context: CallbackContext):
        await payment_history_handler(update, context)
        log_command(update.effective_user, "payment_history")

    async def wrapped_confirm_salary_handler(self, update: Update, context: CallbackContext):
        await confirm_salary_handler(update, context)
        log_command(update.effective_user, "confirm_salary")

    async def handle_dynamic_input(self, update: Update, context: CallbackContext):
        user_data = context.user_data
        user_input = update.message.text
        
        # Логируем ввод пользователя
        user = update.effective_user
        logger.info(f"USER: {user.id} ({user.first_name} @{user.username}) | INPUT: {user_input}")
        
        if user_data.get('awaiting_key'):
            await handle_registration_key(update, context)
        elif user_data.get('awaiting_rate'):
            await handle_hourly_rate(update, context)
        elif user_data.get('awaiting_percent'):
            await handle_percent(update, context)
        elif user_data.get('awaiting_shift_date'):
            await handle_shift_date(update, context)
        elif user_data.get('awaiting_shift_delete'):
            await handle_shift_delete(update, context)
        elif user_data.get('awaiting_hours'):
            await handle_hours_input(update, context)
        elif user_data.get('awaiting_start_revenue'):
            await handle_start_revenue(update, context)
        elif user_data.get('awaiting_end_revenue'):
            await handle_end_revenue(update, context)
        elif user_data.get('awaiting_period'):
            await handle_period_input(update, context)
        else:
            logger.info(f"USER: {user.id} | UNKNOWN_COMMAND: {user_input}")
            await update.message.reply_text("Используйте меню для навигации.")

    def run(self):
        """Запуск бота"""
        logger.info("Bot started successfully")
        self.application.run_polling()

if __name__ == '__main__':
    bot = SalaryBot()
    bot.run()