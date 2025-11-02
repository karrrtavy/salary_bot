from telegram import Update
from telegram.ext import CallbackContext
from bot.database import Database
from bot.utils import validate_date
from bot.keyboards import get_shifts_keyboard, get_main_menu, get_cancel_keyboard
from bot.models import Shift
from datetime import datetime

db = Database()

async def shifts_handler(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "📅 Управление сменами:",
        reply_markup=get_shifts_keyboard()
    )

async def add_shift_handler(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Введите дату смены в формате ГГГГ-ММ-ДД:",
        reply_markup=get_cancel_keyboard()
    )
    context.user_data['awaiting_shift_date'] = True

async def handle_shift_date(update: Update, context: CallbackContext):
    date_str = update.message.text
    
    if not validate_date(date_str):
        await update.message.reply_text("❌ Неверный формат даты! Используйте ГГГГ-ММ-ДД:")
        return
    
    shift_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    # Сохраняем дату смены
    context.user_data['shift_date'] = shift_date
    context.user_data['awaiting_shift_date'] = False
    
    # Сохраняем смену в базу
    user_id = update.effective_user.id
    session = db.get_session()
    try:
        new_shift = Shift(
            user_id=user_id,
            date=shift_date
        )
        session.add(new_shift)
        session.commit()
        context.user_data['current_shift_id'] = new_shift.id
    except Exception as e:
        session.rollback()
        await update.message.reply_text("❌ Ошибка при сохранении смены!")
        return
    finally:
        session.close()
    
    await update.message.reply_text(
        f"✅ Смена на {shift_date} добавлена!",
        reply_markup=get_shifts_keyboard()
    )

async def delete_shift_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    shifts = db.get_user_shifts(user_id)
    
    if not shifts:
        await update.message.reply_text("❌ У вас нет добавленных смен.")
        return
    
    shifts_text = "\n".join([f"{i+1}. {shift.date}" for i, shift in enumerate(shifts)])
    
    await update.message.reply_text(
        f"Ваши смены:\n{shifts_text}\n\nВведите номер смены для удаления:"
    )
    context.user_data['awaiting_shift_delete'] = True
    context.user_data['user_shifts'] = shifts

async def handle_shift_delete(update: Update, context: CallbackContext):
    try:
        shift_num = int(update.message.text) - 1
        shifts = context.user_data['user_shifts']
        
        if 0 <= shift_num < len(shifts):
            shift_to_delete = shifts[shift_num]
            
            session = db.get_session()
            try:
                session.delete(shift_to_delete)
                session.commit()
                await update.message.reply_text("✅ Смена удалена!")
            except Exception as e:
                session.rollback()
                await update.message.reply_text("❌ Ошибка при удалении смены!")
                return
            finally:
                session.close()
        else:
            await update.message.reply_text("❌ Неверный номер смены!")
    
    except ValueError:
        await update.message.reply_text("❌ Введите число!")
    
    context.user_data['awaiting_shift_delete'] = False

async def show_shifts_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    shifts = db.get_user_shifts(user_id)
    
    if not shifts:
        await update.message.reply_text("📭 У вас нет добавленных смен.")
        return
    
    shifts_text = "\n".join([f"• {shift.date} - {'✅' if shift.is_completed else '⏳'}" for shift in shifts])
    
    await update.message.reply_text(f"📋 Ваши смены:\n{shifts_text}")