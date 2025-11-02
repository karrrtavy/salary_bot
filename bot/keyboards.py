from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    keyboard = [
        ['📅 Мои смены', '💰 Расчет зарплаты'],
        ['📊 Текущий период', '📋 Предыдущий период'],
        ['📜 История выплат', '❓ Помощь']
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
        ['📊 Текущий период', '📋 Предыдущий период'],
        ['📜 История выплат', '🔙 Назад']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)