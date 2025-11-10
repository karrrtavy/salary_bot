from sqlalchemy import create_engine, extract, and_, desc, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from .config import DATABASE_URL
from .models import Base, User, RegistrationKey, Shift, PaymentPeriod
import secrets
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        # Используем PostgreSQL connection pool
        self.engine = create_engine(
            DATABASE_URL,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True  # Проверяем соединение перед использованием
        )
        self.Session = sessionmaker(bind=self.engine)
        
        self._safe_initialize()
        self._initialize_keys()

    def _safe_initialize(self):
        """Безопасная инициализация - создает только отсутствующие таблицы и колонки"""
        try:
            inspector = inspect(self.engine)
            existing_tables = inspector.get_table_names()
            
            logger.info(f"🔍 Найдены таблицы: {existing_tables}")
            
            # Создаем все таблицы (SQLAlchemy сама создаст только отсутствующие)
            Base.metadata.create_all(self.engine)
            logger.info("✅ Таблицы проверены/созданы")
            
            # Проверяем и добавляем отсутствующие колонки для существующих таблиц
            self._add_missing_columns()
            
        except Exception as e:
            logger.error(f"❌ Ошибка при инициализации БД: {e}")
            raise e

    def _add_missing_columns(self):
        """Добавляем отсутствующие колонки в существующие таблицы"""
        inspector = inspect(self.engine)
        
        # Проверяем таблицу shifts на наличие новых колонок
        if 'shifts' in inspector.get_table_names():
            existing_columns = [col['name'] for col in inspector.get_columns('shifts')]
            logger.info(f"🔍 Существующие колонки в shifts: {existing_columns}")
            
            # Список необходимых колонок
            required_columns = ['shift_type', 'break_start_revenue', 'break_end_revenue', 'total_revenue']
            
            for column in required_columns:
                if column not in existing_columns:
                    logger.info(f"📋 Добавляем отсутствующую колонку: {column}")
                    try:
                        with self.engine.connect() as conn:
                            if column == 'shift_type':
                                conn.execute(f'ALTER TABLE shifts ADD COLUMN {column} VARCHAR')
                            else:
                                conn.execute(f'ALTER TABLE shifts ADD COLUMN {column} FLOAT')
                            conn.commit()
                        logger.info(f"✅ Колонка {column} добавлена")
                    except Exception as e:
                        logger.error(f"❌ Ошибка при добавлении колонки {column}: {e}")

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
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка при получении пользователя {user_id}: {e}")
            return None
        finally:
            session.close()

    def validate_key(self, key):
        session = self.Session()
        try:
            reg_key = session.query(RegistrationKey).filter_by(key=key, is_used=False).first()
            return reg_key is not None
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка при проверке ключа {key}: {e}")
            return False
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
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"❌ Ошибка при использовании ключа {key}: {e}")
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
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка при получении смен пользователя {user_id}: {e}")
            return []
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
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка при получении завершенных смен пользователя {user_id}: {e}")
            return []
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
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"❌ Ошибка при удалении старых смен: {e}")
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
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка при получении смен за период пользователя {user_id}: {e}")
            return []
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
            logger.error(f"❌ Ошибка при создании периода выплаты: {e}")
            raise e
        finally:
            session.close()

    def get_user_payment_periods(self, user_id, limit=10):
        """Получить историю выплат пользователя"""
        session = self.Session()
        try:
            return session.query(PaymentPeriod).filter_by(user_id=user_id).order_by(PaymentPeriod.created_at.desc()).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка при получении периодов выплат пользователя {user_id}: {e}")
            return []
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
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка при получении периода по дате: {e}")
            return None
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
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка при получении периодов по месяцу: {e}")
            return []
        finally:
            session.close()