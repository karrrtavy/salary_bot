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

def calculate_payment_date(target_day):
    """
    Расчет даты выплаты по правилам:
    - Если 10,20,30 число в сб или вс → выплата в понедельник
    - Если 10,20,30 число с пн по пт → выплата 9,19,29 числа
    """
    today = date.today()
    year = today.year
    month = today.month
    
    # Создаем дату для 10, 20, 30 числа текущего месяца
    target_date = date(year, month, target_day)
    
    # Проверяем день недели (0-пн, 1-вт, 2-ср, 3-чт, 4-пт, 5-сб, 6-вс)
    weekday = target_date.weekday()
    
    if weekday >= 5:  # Суббота или воскресенье
        # Выплата в понедельник
        days_until_monday = (7 - weekday) % 7
        if days_until_monday == 0:  # Если уже понедельник
            days_until_monday = 7
        payment_date = target_date + timedelta(days=days_until_monday)
    else:  # Понедельник-пятница
        # Выплата за день до (9, 19, 29 числа)
        payment_date = target_date - timedelta(days=1)
    
    return payment_date

def get_current_period_dates():
    """Получить даты текущего 10-дневного периода"""
    today = date.today()
    day = today.day
    
    if 1 <= day <= 10:
        period_number = 1
        start_date = date(today.year, today.month, 1)
        end_date = date(today.year, today.month, 10)
        payment_date = calculate_payment_date(10)
    elif 11 <= day <= 20:
        period_number = 2
        start_date = date(today.year, today.month, 11)
        end_date = date(today.year, today.month, 20)
        payment_date = calculate_payment_date(20)
    else:  # 21-31
        period_number = 3
        start_date = date(today.year, today.month, 21)
        # Определяем последний день месяца
        if today.month == 12:
            next_month = date(today.year + 1, 1, 1)
        else:
            next_month = date(today.year, today.month + 1, 1)
        end_date = next_month - timedelta(days=1)
        payment_date = calculate_payment_date(30)
    
    return {
        'period_number': period_number,
        'start_date': start_date,
        'end_date': end_date,
        'payment_date': payment_date
    }

def get_previous_period_dates():
    """Получить даты предыдущего 10-дневного периода"""
    today = date.today()
    day = today.day
    
    if 1 <= day <= 10:
        # Предыдущий период - последние 10 дней прошлого месяца
        if today.month == 1:
            prev_month = date(today.year - 1, 12, 1)
        else:
            prev_month = date(today.year, today.month - 1, 1)
        
        # Последние 10 дней прошлого месяца
        period_number = 3
        start_date = date(prev_month.year, prev_month.month, 21)
        end_date = date(prev_month.year, prev_month.month, 31)
        try:
            end_date = date(prev_month.year, prev_month.month, 31)
        except ValueError:
            try:
                end_date = date(prev_month.year, prev_month.month, 30)
            except ValueError:
                end_date = date(prev_month.year, prev_month.month, 29)
        
        payment_date = calculate_payment_date(30)
        
    elif 11 <= day <= 20:
        period_number = 1
        start_date = date(today.year, today.month, 1)
        end_date = date(today.year, today.month, 10)
        payment_date = calculate_payment_date(10)
    else:  # 21-31
        period_number = 2
        start_date = date(today.year, today.month, 11)
        end_date = date(today.year, today.month, 20)
        payment_date = calculate_payment_date(20)
    
    return {
        'period_number': period_number,
        'start_date': start_date,
        'end_date': end_date,
        'payment_date': payment_date
    }

def format_period_report(period_data, shifts, total_salary):
    """Форматирование отчета за период"""
    period_info = period_data['period_info']
    
    report = f"""
📅 **Отчет за период: {period_info['start_date'].strftime('%d.%m.%Y')} - {period_info['end_date'].strftime('%d.%m.%Y')}**

🔄 Период: {period_info['period_number']}/3
💰 Сумма к выплате: {total_salary:.2f} руб.
📋 Количество смен: {len(shifts)}
📆 Дата выплаты: {period_info['payment_date'].strftime('%d.%m.%Y')}

📊 Детализация смен:
"""
    
    for i, shift in enumerate(shifts, 1):
        report += f"\n{i}. {shift.date.strftime('%d.%m')} - {shift.calculated_salary:.2f} руб."
    
    report += f"\n\n💵 **Итого: {total_salary:.2f} руб.**"
    
    return report