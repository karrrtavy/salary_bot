from sqlalchemy import create_engine, extract
from sqlalchemy.orm import sessionmaker
from .config import DATABASE_URL
from .models import Base, User, RegistrationKey, Shift, PaymentPeriod
import secrets
from datetime import datetime, date, timedelta

class Database:
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._initialize_keys()

    # ... остальные методы остаются без изменений ...

    def get_user_shifts_for_period(self, user_id, start_date, end_date):
        """Получить смены пользователя за определенный период"""
        session = self.Session()
        try:
            return session.query(Shift).filter(
                Shift.user_id == user_id,
                Shift.date >= start_date,
                Shift.date <= end_date,
                Shift.is_completed == True
            ).order_by(Shift.date).all()
        finally:
            session.close()

    def create_payment_period(self, user_id, period_number, start_date, end_date, payment_date, total_salary, shifts_count):
        """Создать запись о периоде выплаты"""
        session = self.Session()
        try:
            payment_period = PaymentPeriod(
                user_id=user_id,
                period_number=period_number,
                start_date=start_date,
                end_date=end_date,
                payment_date=payment_date,
                total_salary=total_salary,
                shifts_count=shifts_count
            )
            session.add(payment_period)
            session.commit()
            return payment_period
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_user_payment_periods(self, user_id, limit=10):
        """Получить историю выплат пользователя"""
        session = self.Session()
        try:
            return session.query(PaymentPeriod).filter_by(user_id=user_id).order_by(PaymentPeriod.created_at.desc()).limit(limit).all()
        finally:
            session.close()

    def get_payment_period_by_date(self, user_id, period_date):
        """Получить период выплаты по дате"""
        session = self.Session()
        try:
            return session.query(PaymentPeriod).filter(
                PaymentPeriod.user_id == user_id,
                PaymentPeriod.start_date <= period_date,
                PaymentPeriod.end_date >= period_date
            ).first()
        finally:
            session.close()