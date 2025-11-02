from telegram import Update
from telegram.ext import CallbackContext
from bot.database import Database
from bot.utils import calculate_salary, format_salary_details, validate_hours, validate_revenue
from bot.utils import validate_period_format, parse_period, format_period_report, get_suggested_periods
from bot.keyboards import get_confirmation_keyboard, get_main_menu, get_periods_keyboard
from bot.models import Shift
from datetime import datetime

db = Database()

async def salary_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = db.get_user_by_id(user_id)
    
    if not user:
        await update.message.reply_text("❌ Сначала зарегистрируйтесь!")
        return
    
    # Получаем текущую смену (последнюю добавленную)
    shifts = db.get_user_shifts(user_id)
    current_shift = None
    
    for shift in reversed(shifts):
        if not shift.is_completed:
            current_shift = shift
            break
    
    if not current_shift:
        await update.message.reply_text("❌ Нет активных смен для расчета!")
        return
    
    context.user_data['current_shift_id'] = current_shift.id
    context.user_data['awaiting_hours'] = True
    
    await update.message.reply_text("⏰ Введите количество отработанных часов (до 14):")

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
    
    await update.message.reply_text(
        format_salary_details(salary_details),
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
    except Exception as e:
        session.rollback()
        await update.message.reply_text("❌ Ошибка при сохранении данных!")
        return
    finally:
        session.close()
    
    await update.message.reply_text(
        "✅ Данные сохранены! Заработок учтен.",
        reply_markup=get_main_menu()
    )
    context.user_data.clear()

async def monthly_report_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    current_date = datetime.now()
    
    shifts = db.get_user_shifts(user_id, current_date.month, current_date.year)
    completed_shifts = [s for s in shifts if s.is_completed]
    
    if not completed_shifts:
        await update.message.reply_text("📭 Нет завершенных смен за текущий месяц.")
        return
    
    total_salary = 0
    report_text = "📊 Отчет за текущий месяц:\n\n"
    
    for shift in completed_shifts:
        report_text += f"📅 {shift.date}\n"
        report_text += f"💸 Заработок: {shift.calculated_salary:.2f} руб.\n"
        report_text += "─" * 20 + "\n"
        total_salary += shift.calculated_salary
    
    report_text += f"\n💰 Итого за месяц: {total_salary:.2f} руб."
    
    await update.message.reply_text(report_text)

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