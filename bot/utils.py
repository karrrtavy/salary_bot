from bot.config import BONUS_TABLE, MAX_HOURLY_RATE, MAX_PERCENT, MAX_HOURS, MAX_REVENUE
from datetime import datetime, date, timedelta
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

def validate_period_format(period_str):
    """Проверка формата периода ГГГГ.ММ.ДД-ГГГГ.ММ.ДД"""
    try:
        if '-' not in period_str:
            return False
        
        start_str, end_str = period_str.split('-')
        start_date = datetime.strptime(start_str, '%Y.%m.%d').date()
        end_date = datetime.strptime(end_str, '%Y.%m.%d').date()
        
        # Проверяем что начальная дата не позже конечной
        if start_date > end_date:
            return False
            
        return True
    except:
        return False

def parse_period(period_str):
    """Парсинг периода из строки"""
    try:
        start_str, end_str = period_str.split('-')
        start_date = datetime.strptime(start_str, '%Y.%m.%d').date()
        end_date = datetime.strptime(end_str, '%Y.%m.%d').date()
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'period_str': period_str
        }
    except:
        return None

def calculate_payment_date_for_period(end_date):
    """
    Расчет даты выплаты для произвольного периода по правилам:
    - Если конечная дата в сб или вс → выплата в понедельник
    - Если конечная дата с пн по пт → выплата за день до
    """
    # Проверяем день недели конечной даты (0-пн, 1-вт, 2-ср, 3-чт, 4-пт, 5-сб, 6-вс)
    weekday = end_date.weekday()
    
    if weekday >= 5:  # Суббота или воскресенье
        # Выплата в понедельник
        days_until_monday = (7 - weekday) % 7
        if days_until_monday == 0:  # Если уже понедельник
            days_until_monday = 7
        payment_date = end_date + timedelta(days=days_until_monday)
    else:  # Понедельник-пятница
        # Выплата за день до конечной даты
        payment_date = end_date - timedelta(days=1)
    
    return payment_date

def format_period_report(period_data, shifts, total_salary):
    """Форматирование отчета за период"""
    start_date = period_data['start_date']
    end_date = period_data['end_date']
    payment_date = calculate_payment_date_for_period(end_date)
    
    report = f"""
📅 **Отчет за период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}**

💰 Сумма к выплате: {total_salary:.2f} руб.
📋 Количество смен: {len(shifts)}
📆 Дата выплаты: {payment_date.strftime('%d.%m.%Y')}

📊 Детализация смен:
"""
    
    for i, shift in enumerate(shifts, 1):
        report += f"\n{i}. {shift.date.strftime('%d.%m.%Y')} - {shift.calculated_salary:.2f} руб."
    
    report += f"\n\n💵 **Итого: {total_salary:.2f} руб.**"
    
    return report

def get_suggested_periods():
    """Получить предложенные периоды (текущий и предыдущий месяцы)"""
    today = date.today()
    current_month = today.month
    current_year = today.year
    
    suggested_periods = []
    
    # Текущий месяц - 3 периода по 10 дней
    if current_month == 12:
        next_year = current_year + 1
        next_month = 1
    else:
        next_year = current_year
        next_month = current_month + 1
    
    # Определяем последний день текущего месяца
    last_day = (date(next_year, next_month, 1) - timedelta(days=1)).day
    
    periods = [
        (1, 10),
        (11, 20),
        (21, last_day)
    ]
    
    for start_day, end_day in periods:
        if start_day <= last_day:  # Проверяем что период существует
            period_str = f"{current_year}.{current_month:02d}.{start_day:02d}-{current_year}.{current_month:02d}.{end_day:02d}"
            suggested_periods.append(period_str)
    
    # Предыдущий месяц
    if current_month == 1:
        prev_year = current_year - 1
        prev_month = 12
    else:
        prev_year = current_year
        prev_month = current_month - 1
    
    # Определяем последний день предыдущего месяца
    prev_last_day = (date(current_year, current_month, 1) - timedelta(days=1)).day
    
    prev_periods = [
        (1, 10),
        (11, 20),
        (21, prev_last_day)
    ]
    
    for start_day, end_day in prev_periods:
        if start_day <= prev_last_day:
            period_str = f"{prev_year}.{prev_month:02d}.{start_day:02d}-{prev_year}.{prev_month:02d}.{end_day:02d}"
            suggested_periods.append(period_str)
    
    return suggested_periods