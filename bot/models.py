from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean
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
    start_revenue = Column(Float)
    end_revenue = Column(Float)
    salary_details = Column(String)  # JSON с детализацией
    calculated_salary = Column(Float)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)