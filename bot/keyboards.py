from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from bot.config import SHIFT_TYPES

def get_main_menu():
    keyboard = [
        ['📅 Мои смены', '💰 Расчет зарплаты'],
        ['📊 Расчет за период', '📜 История выплат'],
        ['❓ Помощь']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_shifts_keyboard():
    keyboard = [
        ['➕ Добавить смену', '➖ Удалить смену'],
        ['📋 Мои смены', '🔙 Назад']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_confirmation_keyboard():
    keyboard = [
        ['✅ Подтвердить', '✏️ Изменить']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_cancel_keyboard():
    keyboard = [
        ['❌ Отмена']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_periods_keyboard():
    keyboard = [
        ['🔙 Назад']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_shift_selection_keyboard(shifts):
    """Клавиатура для выбора смены для расчета"""
    keyboard = []
    
    today = datetime.now().date()
    today_shift = next((shift for shift in shifts if shift.date == today and not shift.is_completed), None)
    
    if today_shift:
        keyboard.append(['📅 Смена за сегодня'])
    
    previous_shifts = [shift for shift in shifts if shift.date < today and not shift.is_completed][:5]
    
    for shift in previous_shifts:
        keyboard.append([f"📋 {shift.date.strftime('%d.%m.%Y')}"])
    
    keyboard.append(['🔙 Назад'])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_shift_types_keyboard():
    """Клавиатура для выбора типа смены (для 2% пользователей)"""
    keyboard = []
    
    for shift_type in SHIFT_TYPES.keys():
        hours = SHIFT_TYPES[shift_type]['hours']
        keyboard.append([f"{shift_type} ({hours} часов)"])
    
    keyboard.append(['🔙 Назад'])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)