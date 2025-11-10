from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, date
import json

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    hourly_rate = Column(Float)
    percent = Column(Integer)
    registration_key = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class RegistrationKey(Base):
    __tablename__ = 'registration_keys'
    
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    is_used = Column(Boolean, default=False)
    used_by = Column(Integer)
    used_at = Column(DateTime)

class Shift(Base):
    __tablename__ = 'shifts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    date = Column(Date)
    hours_worked = Column(Float)
    shift_type = Column(String)  # Новое поле: тип смены
    start_revenue = Column(Float)
    end_revenue = Column(Float)
    # Новые поля для 2% пользователей
    revenue_come1 = Column(Float)    # Выручка при приходе
    revenue_leave1 = Column(Float)   # Выручка при уходе (первый раз)
    revenue_come2 = Column(Float)    # Выручка при возвращении
    revenue_leave2 = Column(Float)   # Выручка при окончательном уходе
    total_revenue = Column(Float)    # Общая выручка (для смен до 21:00)
    had_break = Column(Boolean)      # Был ли перерыв
    salary_details = Column(Text)    # Изменено на Text для больших JSON
    calculated_salary = Column(Float)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class PaymentPeriod(Base):
    __tablename__ = 'payment_periods'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    period_number = Column(Integer)  # 1, 2, 3 для 10, 20, 30 дней
    start_date = Column(Date)
    end_date = Column(Date)
    payment_date = Column(Date)  # Дата когда должна быть выплата
    total_salary = Column(Float)
    shifts_count = Column(Integer)
    is_paid = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)