from bot.database import Database
from bot.models import Base
import logging
from sqlalchemy import inspect

logger = logging.getLogger(__name__)

def migrate_database():
    """Добавляем недостающие колонки в таблицу shifts"""
    db = Database()
    engine = db.engine
    
    # Используем правильный способ получения инспектора
    inspector = inspect(engine)
    existing_columns = [col['name'] for col in inspector.get_columns('shifts')]
    
    logger.info(f"🔍 Существующие колонки в shifts: {existing_columns}")
    
    # Список новых колонок для добавления
    new_columns = [
        'shift_type',
        'revenue_come1', 
        'revenue_leave1',
        'revenue_come2',
        'revenue_leave2', 
        'total_revenue',
        'had_break'
    ]
    
    missing_columns = [col for col in new_columns if col not in existing_columns]
    
    if missing_columns:
        logger.info(f"📋 Добавляем отсутствующие колонки: {missing_columns}")
        
        # Создаем ALTER TABLE запросы для каждой отсутствующей колонки
        with engine.connect() as conn:
            for column in missing_columns:
                try:
                    if column == 'shift_type':
                        conn.execute(f"ALTER TABLE shifts ADD COLUMN {column} VARCHAR")
                    elif column == 'had_break':
                        conn.execute(f"ALTER TABLE shifts ADD COLUMN {column} BOOLEAN")
                    else:
                        conn.execute(f"ALTER TABLE shifts ADD COLUMN {column} FLOAT")
                    logger.info(f"✅ Добавлена колонка: {column}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при добавлении колонки {column}: {e}")
            
            conn.commit()
        
        logger.info("✅ Миграция базы данных завершена")
    else:
        logger.info("✅ Все необходимые колонки уже существуют")

if __name__ == '__main__':
    migrate_database()