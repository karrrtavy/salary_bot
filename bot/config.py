import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

# Для Railway используем DATABASE_URL из окружения, для локальной разработки - PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    # Локальная разработка с PostgreSQL
    DATABASE_URL = f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'postgres')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'salary_bot')}"

# Константы
MAX_HOURLY_RATE = 500
MAX_PERCENT = 5
MAX_HOURS = 14
MAX_REVENUE = 200000

BONUS_TABLE = {
    0: 0,
    5000: 100,
    10000: 200,
    15000: 300,
    20000: 400,
    25000: 500,
    30000: 600,
    35000: 700,
    40000: 800,
    45000: 900,
    50000: 1000,
    55000: 1100,
    60000: 1200,
    65000: 1300,
    70000: 1400,
    75000: 1500,
    80000: 1600,
    85000: 1700,
    90000: 1800,
    95000: 1900,
    100000: 2000
}

# Смены для 2% пользователей
SHIFT_TYPES = {
    '8-20': {'hours': 12, 'needs_break': True},
    '8-21': {'hours': 13, 'needs_break': False},
    '9-21': {'hours': 12, 'needs_break': False},
    '9-20': {'hours': 11, 'needs_break': True}
}