import logging
import os
import sys
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext
from telegram import Update

from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram import Update

from bot.handlers.salary import current_period_handler, previous_period_handler, payment_history_handler

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.config import BOT_TOKEN
from bot.database import Database
from bot.handlers.start import start_handler, help_handler
from bot.handlers.registration import handle_registration_key, handle_hourly_rate, handle_percent
from bot.handlers.shifts import shifts_handler, add_shift_handler, handle_shift_date, delete_shift_handler, handle_shift_delete, show_shifts_handler
from bot.handlers.salary import salary_handler, handle_hours_input, handle_start_revenue, handle_end_revenue, confirm_salary_handler, monthly_report_handler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SalaryBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.db = Database()
        self.setup_handlers()

    def setup_handlers(self):
        # Команды
        self.application.add_handler(CommandHandler("start", start_handler))
        self.application.add_handler(CommandHandler("help", help_handler))
        
        # Обработчики меню
        self.application.add_handler(MessageHandler(filters.Text(["❓ Помощь"]), help_handler))
        self.application.add_handler(MessageHandler(filters.Text(["📅 Мои смены"]), shifts_handler))
        self.application.add_handler(MessageHandler(filters.Text(["➕ Добавить смену"]), add_shift_handler))
        self.application.add_handler(MessageHandler(filters.Text(["➖ Удалить смену"]), delete_shift_handler))
        self.application.add_handler(MessageHandler(filters.Text(["📋 Мои смены"]), show_shifts_handler))
        self.application.add_handler(MessageHandler(filters.Text(["🔙 Назад"]), start_handler))
        self.application.add_handler(MessageHandler(filters.Text(["💰 Расчет зарплаты"]), salary_handler))
        
        # Новые обработчики периодов
        self.application.add_handler(MessageHandler(filters.Text(["📊 Текущий период"]), current_period_handler))
        self.application.add_handler(MessageHandler(filters.Text(["📋 Предыдущий период"]), previous_period_handler))
        self.application.add_handler(MessageHandler(filters.Text(["📜 История выплат"]), payment_history_handler))
        
        self.application.add_handler(MessageHandler(filters.Text(["✅ Подтвердить"]), confirm_salary_handler))
        self.application.add_handler(MessageHandler(filters.Text(["✏️ Изменить"]), salary_handler))
        self.application.add_handler(MessageHandler(filters.Text(["❌ Отмена"]), start_handler))
        
        # Динамические обработчики
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handle_dynamic_input
        ))

    async def handle_dynamic_input(self, update: Update, context: CallbackContext):
        user_data = context.user_data
        
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
        else:
            await update.message.reply_text("Используйте меню для навигации.")

    def run(self):
        """Запуск бота"""
        self.application.run_polling()

if __name__ == '__main__':
    bot = SalaryBot()
    bot.run()