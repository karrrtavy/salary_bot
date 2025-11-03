from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

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
    
    # Добавляем кнопку "Сегодня" если есть смена на сегодня
    today = datetime.now().date()
    today_shift = next((shift for shift in shifts if shift.date == today and not shift.is_completed), None)
    
    if today_shift:
        keyboard.append(['📅 Смена за сегодня'])
    
    # Добавляем кнопки для предыдущих смен (максимум 5)
    previous_shifts = [shift for shift in shifts if shift.date < today and not shift.is_completed][:5]
    
    for shift in previous_shifts:
        keyboard.append([f"📋 {shift.date.strftime('%d.%m.%Y')}"])
    
    keyboard.append(['🔙 Назад'])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_shift_type_keyboard():
    """Клавиатура для выбора типа смены (для 2% пользователей)"""
    keyboard = [
        ['🕗 8:00-20:00', '🕗 8:00-21:00'],
        ['🕘 9:00-20:00', '🕘 9:00-21:00'],
        ['🔙 Назад']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_break_question_keyboard():
    """Клавиатура для вопроса об уходе со смены"""
    keyboard = [
        ['✅ Да, уходил', '❌ Нет, не уходил'],
        ['🔙 Назад']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)