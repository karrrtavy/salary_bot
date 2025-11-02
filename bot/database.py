from sqlalchemy import create_engine, extract
from sqlalchemy.orm import sessionmaker
from .config import DATABASE_URL
from .models import Base, User, RegistrationKey, Shift
import secrets
from datetime import datetime, date

class Database:
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._initialize_keys()

    def _initialize_keys(self):
        """Инициализация 10 ключей при первом запуске"""
        session = self.Session()
        try:
            existing_keys = session.query(RegistrationKey).count()
            if existing_keys == 0:
                for _ in range(10):
                    key = secrets.token_hex(4).upper()
                    reg_key = RegistrationKey(key=key)
                    session.add(reg_key)
                session.commit()
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