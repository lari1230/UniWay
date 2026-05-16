import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8719146651:AAFZ4L2Bo9q1ohPWpbvszr-A-D3tRS2mTXw")

# Настройки SQL Server Express
SQL_SERVER_CONFIG = {
    'server': os.getenv('SQL_SERVER', 'DESKTOP-RGO1G1M\SQLEXPRESS'),  # или .\SQLEXPRESS
    'database': os.getenv('SQL_DATABASE', 'uniway_bot'),
    'driver': os.getenv('SQL_DRIVER', '{ODBC Driver 17 for SQL Server}'),
    'trusted_connection': os.getenv('SQL_TRUSTED_CONNECTION', 'yes'),  # Windows аутентификация
    # Если используете логин/пароль вместо Windows аутентификации:
    'username': os.getenv('SQL_USERNAME', ''),
    'password': os.getenv('SQL_PASSWORD', '')
}

# Предметы
SUBJECTS = {
    "math": {"name": "📐 Математика", "emoji": "📐"},
    "russian": {"name": "📖 Русский язык", "emoji": "📖"},
    "history": {"name": "🏛️ История", "emoji": "🏛️"}
}

# Сложности
DIFFICULTY_LEVELS = {
    "easy": {"name": "🟢 Легкий", "value": 1},
    "medium": {"name": "🟡 Средний", "value": 2},
    "hard": {"name": "🔴 Сложный", "value": 3}
}

# Темы по предметам
TOPICS = {
    "math": [
        "Квадратные уравнения",
        "Производные",
        "Логарифмы",
        "Тригонометрия",
        "Планиметрия",
        "Стереометрия",
        "Неравенства",
        "Прогрессии",
        "Комбинаторика"
    ],
    "russian": [
        "Правописание корней",
        "Приставки",
        "Суффиксы",
        "НЕ с разными частями речи",
        "Пунктуация",
        "Грамматика",
        "Лексика",
        "Стилистика",
        "Средства выразительности"
    ],
    "history": [
        "Древняя Русь",
        "Монгольское нашествие",
        "Иван Грозный",
        "Смутное время",
        "Петр I",
        "Екатерина II",
        "Отечественная война 1812 года",
        "Реформы Александра II",
        "Первая мировая война",
        "Великая Отечественная война"
    ]
}
