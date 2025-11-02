from telegram import Update
from telegram.ext import CallbackContext
from bot.database import Database
from bot.utils import validate_hourly_rate, validate_percent, log_user_action
from bot.keyboards import get_main_menu, get_cancel_keyboard
from bot.models import User
import logging

logger = logging.getLogger(__name__)

db = Database()

async def handle_registration_key(update: Update, context: CallbackContext):
    key = update.message.text.upper().strip()
    user = update.effective_user
    
    log_user_action(user.id, "REGISTRATION_KEY_INPUT", f"key: {key}")
    
    if not db.validate_key(key):
        logger.warning(f"USER: {user.id} | INVALID_KEY: {key}")
        await update.message.reply_text("❌ Неверный или уже использованный ключ. Попробуйте еще раз:")
        return
    
    context.user_data['registration_key'] = key
    context.user_data['awaiting_key'] = False
    context.user_data['awaiting_rate'] = True
    
    logger.info(f"USER: {user.id} | KEY_VALIDATED: {key}")
    await update.message.reply_text(
        "✅ Ключ принят! Теперь введите вашу ставку в час (до 500 руб.):",
        reply_markup=get_cancel_keyboard()
    )

async def handle_hourly_rate(update: Update, context: CallbackContext):
    rate_text = update.message.text
    user = update.effective_user
    
    log_user_action(user.id, "HOURLY_RATE_INPUT", f"rate: {rate_text}")
    
    if not validate_hourly_rate(rate_text):
        logger.warning(f"USER: {user.id} | INVALID_RATE: {rate_text}")
        await update.message.reply_text("❌ Неверная ставка! Введите число до 500:")
        return
    
    context.user_data['hourly_rate'] = float(rate_text)
    context.user_data['awaiting_rate'] = False
    context.user_data['awaiting_percent'] = True
    
    logger.info(f"USER: {user.id} | RATE_ACCEPTED: {rate_text}")
    await update.message.reply_text("📊 Теперь введите ваш процент с выручки (1-5%):")

async def handle_percent(update: Update, context: CallbackContext):
    percent_text = update.message.text
    user = update.effective_user
    
    log_user_action(user.id, "PERCENT_INPUT", f"percent: {percent_text}")
    
    if not validate_percent(percent_text):
        logger.warning(f"USER: {user.id} | INVALID_PERCENT: {percent_text}")
        await update.message.reply_text("❌ Неверный процент! Введите число от 1 до 5:")
        return
    
    key = context.user_data['registration_key']
    hourly_rate = context.user_data['hourly_rate']
    percent = int(percent_text)
    
    # Сохраняем пользователя
    if not db.use_key(key, user.id):
        logger.error(f"USER: {user.id} | KEY_USAGE_FAILED: {key}")
        await update.message.reply_text("❌ Ошибка при использовании ключа!")
        return
    
    session = db.get_session()
    try:
        new_user = User(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            hourly_rate=hourly_rate,
            percent=percent,
            registration_key=key
        )
        session.add(new_user)
        session.commit()
        logger.info(f"USER: {user.id} | REGISTRATION_COMPLETED: rate={hourly_rate}, percent={percent}")
    except Exception as e:
        session.rollback()
        logger.error(f"USER: {user.id} | REGISTRATION_ERROR: {str(e)}")
        await update.message.reply_text("❌ Ошибка при сохранении данных!")
        return
    finally:
        session.close()
    
    # Очищаем временные данные
    context.user_data.clear()
    
    await update.message.reply_text(
        f"✅ Регистрация завершена!\n"
        f"💰 Ваша ставка: {hourly_rate} руб./час\n"
        f"📊 Ваш процент: {percent}%\n\n"
        f"Теперь вы можете добавлять смены и рассчитывать заработок.",
        reply_markup=get_main_menu()
    )