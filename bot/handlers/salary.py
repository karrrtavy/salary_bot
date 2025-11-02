from telegram import Update
from telegram.ext import CallbackContext
from bot.database import Database
from bot.utils import calculate_salary, format_salary_details, validate_hours, validate_revenue
from bot.keyboards import get_confirmation_keyboard, get_main_menu
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