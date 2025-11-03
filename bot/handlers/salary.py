from telegram import Update
from telegram.ext import CallbackContext
from bot.database import Database
from bot.utils import calculate_salary, format_salary_details, validate_hours, validate_revenue
from bot.utils import validate_period_format, parse_period, format_period_report, get_suggested_periods
from bot.keyboards import get_confirmation_keyboard, get_main_menu, get_periods_keyboard
from bot.models import Shift
from datetime import datetime

db = Database()

from telegram import Update
from telegram.ext import CallbackContext
from bot.database import Database
from bot.utils import calculate_salary, format_salary_details, validate_hours, validate_revenue
from bot.utils import validate_period_format, parse_period, format_period_report, get_suggested_periods
from bot.keyboards import get_confirmation_keyboard, get_main_menu, get_periods_keyboard, get_shift_selection_keyboard
from bot.models import Shift
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

db = Database()

async def salary_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = db.get_user_by_id(user_id)
    
    if not user:
        await update.message.reply_text("❌ Сначала зарегистрируйтесь!")
        return
    
    # Получаем все незавершенные смены пользователя
    shifts = db.get_user_shifts(user_id)
    incomplete_shifts = [shift for shift in shifts if not shift.is_completed and shift.date <= date.today()]
    
    if not incomplete_shifts:
        await update.message.reply_text(
            "❌ Нет незавершенных смен для расчета!\n"
            "Добавьте смену через меню '📅 Мои смены'",
            reply_markup=get_main_menu()
        )
        return
    
    # Сохраняем список смен в user_data для последующего использования
    context.user_data['available_shifts'] = incomplete_shifts
    
    # Создаем клавиатуру для выбора смены
    keyboard = get_shift_selection_keyboard(incomplete_shifts)
    
    await update.message.reply_text(
        "📅 Выберите смену для расчета заработка:",
        reply_markup=keyboard
    )

async def handle_shift_selection(update: Update, context: CallbackContext):
    """Обработчик выбора конкретной смены"""
    user_input = update.message.text
    user_id = update.effective_user.id
    user = db.get_user_by_id(user_id)
    
    # Логируем выбор пользователя
    logger.info(f"USER: {user_id} | SHIFT_SELECTION: {user_input}")
    
    shifts = context.user_data.get('available_shifts', [])
    
    selected_shift = None
    
    if user_input == "📅 Смена за сегодня":
        today = date.today()
        selected_shift = next((shift for shift in shifts if shift.date == today), None)
    elif user_input.startswith("📋 "):
        # Извлекаем дату из текста кнопки (формат: "📋 03.11.2025")
        date_str = user_input[3:]  # Убираем "📋 "
        try:
            selected_date = datetime.strptime(date_str, '%d.%m.%Y').date()
            selected_shift = next((shift for shift in shifts if shift.date == selected_date), None)
        except ValueError:
            await update.message.reply_text("❌ Ошибка при разборе даты!")
            return
    
    if not selected_shift:
        await update.message.reply_text("❌ Выбранная смена не найдена!")
        return
    
    # Сохраняем выбранную смену в контексте
    context.user_data['current_shift_id'] = selected_shift.id
    context.user_data['selected_shift_date'] = selected_shift.date
    context.user_data['awaiting_hours'] = True
    
    # Очищаем временные данные
    context.user_data.pop('available_shifts', None)
    
    await update.message.reply_text(
        f"📅 Выбрана смена за {selected_shift.date.strftime('%d.%m.%Y')}\n\n"
        f"⏰ Введите количество отработанных часов (до 14):"
    )

async def handle_hours_input(update: Update, context: CallbackContext):
    hours_text = update.message.text
    
    if not validate_hours(hours_text):
        await update.message.reply_text("❌ Неверное количество часов! Введите число до 14:")
        return
    
    context.user_data['hours'] = float(hours_text)
    context.user_data['awaiting_hours'] = False
    
    user_id = update.effective_user.id
    user = db.get_user_by_id(user_id)
    
    if user.percent == 1:
        context.user_data['awaiting_end_revenue'] = True
        await update.message.reply_text("💵 Введите выручку за смену:")
    else:
        context.user_data['awaiting_start_revenue'] = True
        await update.message.reply_text("💵 Введите начальную выручку (при начале смены):")

async def handle_start_revenue(update: Update, context: CallbackContext):
    revenue_text = update.message.text
    
    if not validate_revenue(revenue_text):
        await update.message.reply_text("❌ Неверная сумма! Введите число до 200000:")
        return
    
    context.user_data['start_revenue'] = float(revenue_text)
    context.user_data['awaiting_start_revenue'] = False
    context.user_data['awaiting_end_revenue'] = True
    
    await update.message.reply_text("💵 Теперь введите конечную выручку (в конце смены):")

async def handle_end_revenue(update: Update, context: CallbackContext):
    revenue_text = update.message.text
    
    if not validate_revenue(revenue_text):
        await update.message.reply_text("❌ Неверная сумма! Введите число до 200000:")
        return
    
    context.user_data['end_revenue'] = float(revenue_text)
    context.user_data['awaiting_end_revenue'] = False
    
    # Расчет заработка
    user_id = update.effective_user.id
    user = db.get_user_by_id(user_id)
    
    start_revenue = context.user_data.get('start_revenue', 0)
    salary_details = calculate_salary(
        context.user_data['hours'],
        user.hourly_rate,
        user.percent,
        start_revenue,
        context.user_data['end_revenue']
    )
    
    context.user_data['salary_details'] = salary_details
    
    # Добавляем дату смены в детализацию
    shift_date = context.user_data.get('selected_shift_date', date.today())
    
    await update.message.reply_text(
        f"📅 Смена за {shift_date.strftime('%d.%m.%Y')}\n"
        f"{format_salary_details(salary_details)}",
        reply_markup=get_confirmation_keyboard()
    )

async def confirm_salary_handler(update: Update, context: CallbackContext):
    shift_id = context.user_data['current_shift_id']
    salary_details = context.user_data['salary_details']
    
    session = db.get_session()
    try:
        shift = session.query(Shift).filter_by(id=shift_id).first()
        if shift:
            shift.hours_worked = salary_details['hours']
            shift.start_revenue = salary_details.get('start_revenue', 0)
            shift.end_revenue = salary_details['end_revenue']
            shift.calculated_salary = salary_details['total_salary']
            shift.salary_details = str(salary_details)
            shift.is_completed = True
            session.commit()
            
            # Логируем успешное сохранение
            logger.info(f"USER: {update.effective_user.id} | SHIFT_COMPLETED: "
                       f"date={shift.date}, salary={salary_details['total_salary']:.2f}")
    except Exception as e:
        session.rollback()
        logger.error(f"USER: {update.effective_user.id} | SHIFT_SAVE_ERROR: {str(e)}")
        await update.message.reply_text("❌ Ошибка при сохранении данных!")
        return
    finally:
        session.close()
    
    await update.message.reply_text(
        "✅ Данные сохранены! Заработок учтен.",
        reply_markup=get_main_menu()
    )
    context.user_data.clear()

# ... остальные функции без изменений (monthly_report_handler, custom_period_handler, handle_period_input, payment_history_handler) ...
async def custom_period_handler(update: Update, context: CallbackContext):
    """Обработчик выбора произвольного периода"""
    user_id = update.effective_user.id
    user = db.get_user_by_id(user_id)
    
    if not user:
        await update.message.reply_text("❌ Сначала зарегистрируйтесь!")
        return
    
    # Получаем предложенные периоды
    suggested_periods = get_suggested_periods()
    
    message = """
📅 **Расчет заработка за период**

Введите период в формате:
`ГГГГ.ММ.ДД-ГГГГ.ММ.ДД`

Например: `2025.11.01-2025.11.10`

Или выберите один из предложенных периодов:
"""
    
    for i, period in enumerate(suggested_periods, 1):
        start_str, end_str = period.split('-')
        start_date = datetime.strptime(start_str, '%Y.%m.%d').date()
        end_date = datetime.strptime(end_str, '%Y.%m.%d').date()
        message += f"\n{i}. {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
    
    message += "\n\nПросто отправьте номер периода или введите свой в указанном формате."
    
    context.user_data['awaiting_period'] = True
    context.user_data['suggested_periods'] = suggested_periods
    
    await update.message.reply_text(message, parse_mode='Markdown', reply_markup=get_periods_keyboard())

async def handle_period_input(update: Update, context: CallbackContext):
    """Обработчик ввода периода"""
    user_input = update.message.text.strip()
    suggested_periods = context.user_data.get('suggested_periods', [])
    
    # Проверяем, не выбрал ли пользователь номер из предложенных периодов
    if user_input.isdigit():
        period_num = int(user_input)
        if 1 <= period_num <= len(suggested_periods):
            period_str = suggested_periods[period_num - 1]
        else:
            await update.message.reply_text("❌ Неверный номер периода. Попробуйте еще раз:")
            return
    else:
        period_str = user_input
    
    # Проверяем формат периода
    if not validate_period_format(period_str):
        await update.message.reply_text(
            "❌ Неверный формат периода!\n\n"
            "Используйте формат: `ГГГГ.ММ.ДД-ГГГГ.ММ.ДД`\n"
            "Например: `2025.11.01-2025.11.10`",
            parse_mode='Markdown'
        )
        return
    
    # Парсим период
    period_data = parse_period(period_str)
    if not period_data:
        await update.message.reply_text("❌ Ошибка при разборе дат. Проверьте формат.")
        return
    
    user_id = update.effective_user.id
    
    # Получаем смены за указанный период
    shifts = db.get_user_shifts_for_period(
        user_id, 
        period_data['start_date'], 
        period_data['end_date']
    )
    
    if not shifts:
        await update.message.reply_text(
            f"📭 Нет завершенных смен за период "
            f"{period_data['start_date'].strftime('%d.%m.%Y')} - {period_data['end_date'].strftime('%d.%m.%Y')}"
        )
        context.user_data['awaiting_period'] = False
        return
    
    # Считаем общую сумму
    total_salary = sum(shift.calculated_salary for shift in shifts)
    
    # Формируем отчет
    report = format_period_report(period_data, shifts, total_salary)
    
    # Сохраняем данные для возможного подтверждения
    context.user_data['current_period_data'] = {
        'period_data': period_data,
        'shifts': shifts,
        'total_salary': total_salary
    }
    
    await update.message.reply_text(report, parse_mode='Markdown')
    context.user_data['awaiting_period'] = False

async def payment_history_handler(update: Update, context: CallbackContext):
    """Показать историю выплат"""
    user_id = update.effective_user.id
    user = db.get_user_by_id(user_id)
    
    if not user:
        await update.message.reply_text("❌ Сначала зарегистрируйтесь!")
        return
    
    # Получаем историю выплат
    payment_periods = db.get_user_payment_periods(user_id)
    
    if not payment_periods:
        await update.message.reply_text("📭 У вас еще нет завершенных периодов выплат.")
        return
    
    history_text = "📋 **История выплат:**\n\n"
    
    for i, period in enumerate(payment_periods, 1):
        status = "✅ Выплачено" if period.is_paid else "⏳ Ожидает выплаты"
        history_text += (
            f"{i}. {period.start_date.strftime('%d.%m.%Y')}-{period.end_date.strftime('%d.%m.%Y')}\n"
            f"   💰 {period.total_salary:.2f} руб. | 📅 {period.payment_date.strftime('%d.%m.%Y')} | {status}\n\n"
        )
    
    await update.message.reply_text(history_text, parse_mode='Markdown')