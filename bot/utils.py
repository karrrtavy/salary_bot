from bot.config import BONUS_TABLE, MAX_HOURLY_RATE, MAX_PERCENT, MAX_HOURS, MAX_REVENUE
from datetime import datetime, date
import re

def validate_hourly_rate(rate):
    try:
        rate = float(rate)
        return 0 < rate <= MAX_HOURLY_RATE
    except:
        return False

def validate_percent(percent):
    try:
        percent = int(percent)
        return 0 < percent <= MAX_PERCENT
    except:
        return False

def validate_hours(hours):
    try:
        hours = float(hours)
        return 0 < hours <= MAX_HOURS
    except:
        return False

def validate_revenue(revenue):
    try:
        revenue = float(revenue)
        return 0 <= revenue <= MAX_REVENUE
    except:
        return False

def validate_date(date_str):
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except:
        return False

def calculate_bonus(revenue):
    """Расчет бонуса по таблице"""
    bonus = 0
    for threshold, threshold_bonus in sorted(BONUS_TABLE.items()):
        if revenue >= threshold:
            bonus = threshold_bonus
            continue
        return bonus / 2  # Бонус делится на 2
    return 0

def calculate_salary(hours, hourly_rate, percent, start_revenue, end_revenue):
    """Расчет заработка"""
    base_salary = hours * hourly_rate
    
    if percent == 1:
        revenue_share = end_revenue * (percent / 100)
    else:
        revenue_share = (end_revenue - start_revenue) * (percent / 100)
    
    bonus = calculate_bonus(end_revenue)
    total_salary = base_salary + revenue_share + bonus
    
    return {
        'base_salary': base_salary,
        'revenue_share': revenue_share,
        'bonus': bonus,
        'total_salary': total_salary,
        'hours': hours,
        'hourly_rate': hourly_rate,
        'percent': percent,
        'start_revenue': start_revenue,
        'end_revenue': end_revenue
    }

def format_salary_details(details):
    return f"""
🧮 Детализация заработка:

⏰ Отработано часов: {details['hours']}
💰 Ставка в час: {details['hourly_rate']} руб.
📊 Процент с выручки: {details['percent']}%
💵 Выручка за смену: {details['end_revenue']} руб.
🎁 Бонус с выручки: {details['bonus']} руб.

💸 Итоговый заработок: {details['total_salary']:.2f} руб.
    """