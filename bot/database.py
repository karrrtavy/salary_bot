from sqlalchemy import create_engine, extract, and_, desc, inspect
from sqlalchemy.orm import sessionmaker
from .config import DATABASE_URL
from .models import Base, User, RegistrationKey, Shift, PaymentPeriod
import secrets
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
        
        # НЕ создаем таблицы автоматически - проверяем существующие
        self._safe_initialize()
        self._initialize_keys()

    def _safe_initialize(self):
        """Безопасная инициализация - создает только отсутствующие таблицы"""
        inspector = inspect(self.engine)
        existing_tables = inspector.get_table_names()
        
        logger.info(f"🔍 Найдены таблицы: {existing_tables}")
        
        # Список необходимых таблиц
        required_tables = ['users', 'registration_keys', 'shifts', 'payment_periods']
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            logger.info(f"📋 Создаем отсутствующие таблицы: {missing_tables}")
            # Создаем только отсутствующие таблицы
            Base.metadata.create_all(self.engine, tables=[
                Base.metadata.tables[table] for table in missing_tables
            ])
        else:
            logger.info("✅ Все таблицы уже существуют")

    def _initialize_keys(self):
        """Инициализация ключей только если их нет"""
        session = self.Session()
        try:
            existing_keys = session.query(RegistrationKey).filter_by(is_used=False).count()
            if existing_keys == 0:
                logger.info("🔑 Создаем 10 регистрационных ключей...")
                for _ in range(10):
                    key = secrets.token_hex(4).upper()
                    reg_key = RegistrationKey(key=key)
                    session.add(reg_key)
                session.commit()
                logger.info("✅ 10 ключей создано")
            else:
                logger.info(f"🔑 Найдено {existing_keys} неиспользованных ключей")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при инициализации ключей: {str(e)}")
            session.rollback()
        finally:
            session.close()

    def get_session(self):
        return self.Session()

    def get_user_by_id(self, user_id):
        session = self.Session()
        try:
            return session.query(User).filter_by(user_id=user_id).first()
        finally:
            session.close()

    def validate_key(self, key):
        session = self.Session()
        try:
            reg_key = session.query(RegistrationKey).filter_by(key=key, is_used=False).first()
            return reg_key is not None
        finally:
            session.close()

    def use_key(self, key, user_id):
        session = self.Session()
        try:
            reg_key = session.query(RegistrationKey).filter_by(key=key).first()
            if reg_key and not reg_key.is_used:
                reg_key.is_used = True
                reg_key.used_by = user_id
                reg_key.used_at = datetime.utcnow()
                session.commit()
                return True
            return False
        finally:
            session.close()

    def get_user_shifts(self, user_id, month=None, year=None):
        session = self.Session()
        try:
            query = session.query(Shift).filter_by(user_id=user_id)
            if month and year:
                query = query.filter(
                    extract('month', Shift.date) == month,
                    extract('year', Shift.date) == year
                )
            return query.order_by(Shift.date).all()
        finally:
            session.close()

    def get_completed_shifts(self, user_id, limit=20):
        """Получить завершенные смены пользователя (последние limit)"""
        session = self.Session()
        try:
            return session.query(Shift).filter(
                Shift.user_id == user_id,
                Shift.is_completed == True
            ).order_by(Shift.date.desc()).limit(limit).all()
        finally:
            session.close()

    def delete_old_shifts(self):
        """Удаление смен прошлых месяцев"""
        session = self.Session()
        try:
            current_date = date.today()
            session.query(Shift).filter(
                extract('month', Shift.date) < current_date.month,
                extract('year', Shift.date) <= current_date.year
            ).delete()
            session.commit()
        finally:
            session.close()
    
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
        """Получить период выплаты по дате смены"""
        session = self.Session()
        try:
            return session.query(PaymentPeriod).filter(
                PaymentPeriod.user_id == user_id,
                PaymentPeriod.start_date <= period_date,
                PaymentPeriod.end_date >= period_date
            ).first()
        finally:
            session.close()

    def get_payment_periods_by_month(self, user_id, month, year):
        """Получить периоды выплат за конкретный месяц"""
        session = self.Session()
        try:
            return session.query(PaymentPeriod).filter(
                PaymentPeriod.user_id == user_id,
                extract('month', PaymentPeriod.start_date) == month,
                extract('year', PaymentPeriod.start_date) == year
            ).order_by(PaymentPeriod.period_number).all()
        finally:
            session.close()