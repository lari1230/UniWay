import pyodbc
import urllib.parse
from config import SQL_SERVER_CONFIG

def test_connection():
    """Тестирует подключение к SQL Server"""
    
    # Формируем строку подключения
    if SQL_SERVER_CONFIG.get('trusted_connection', '').lower() == 'yes':
        conn_str = (
            f"DRIVER={SQL_SERVER_CONFIG['driver']};"
            f"SERVER={SQL_SERVER_CONFIG['server']};"
            f"Trusted_Connection=yes;"
        )
    else:
        conn_str = (
            f"DRIVER={SQL_SERVER_CONFIG['driver']};"
            f"SERVER={SQL_SERVER_CONFIG['server']};"
            f"UID={SQL_SERVER_CONFIG['username']};"
            f"PWD={SQL_SERVER_CONFIG['password']};"
        )
    
    print("Проверка подключения...")
    print(f"Строка подключения: {conn_str[:100]}...")
    
    try:
        # Пробуем подключиться
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Получаем версию SQL Server
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print(f"✅ Успешное подключение к SQL Server!")
        print(f"Версия: {version[:100]}...")
        
        cursor.close()
        conn.close()
        return True
        
    except pyodbc.Error as e:
        print(f"❌ Ошибка подключения: {e}")
        print("\nВозможные решения:")
        print("1. Убедитесь, что SQL Server Express запущен")
        print("2. Проверьте имя сервера в .env файле")
        print("   Для локального SQL Server Express: SQL_SERVER=localhost\\SQLEXPRESS")
        print("3. Убедитесь, что установлен ODBC Driver 17 для SQL Server")
        print("   Скачайте с: https://go.microsoft.com/fwlink/?linkid=2249006")
        print("4. Включите TCP/IP протокол в SQL Server Configuration Manager")
        return False

def create_database():
    """Создает базу данных SQL Server если она не существует"""
    
    # Формируем строку подключения к master
    if SQL_SERVER_CONFIG.get('trusted_connection', '').lower() == 'yes':
        conn_str = (
            f"DRIVER={SQL_SERVER_CONFIG['driver']};"
            f"SERVER={SQL_SERVER_CONFIG['server']};"
            f"Trusted_Connection=yes;"
        )
    else:
        conn_str = (
            f"DRIVER={SQL_SERVER_CONFIG['driver']};"
            f"SERVER={SQL_SERVER_CONFIG['server']};"
            f"UID={SQL_SERVER_CONFIG['username']};"
            f"PWD={SQL_SERVER_CONFIG['password']};"
        )
    
    try:
        # Подключаемся к master
        conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()
        
        # Проверяем существует ли база данных
        cursor.execute(f"SELECT 1 FROM sys.databases WHERE name = '{SQL_SERVER_CONFIG['database']}'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f"CREATE DATABASE [{SQL_SERVER_CONFIG['database']}]")
            print(f"✅ База данных '{SQL_SERVER_CONFIG['database']}' создана")
        else:
            print(f"✅ База данных '{SQL_SERVER_CONFIG['database']}' уже существует")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Настройка SQL Server для бота UniWay")
    print("=" * 50)
    print(f"Сервер: {SQL_SERVER_CONFIG['server']}")
    print(f"База данных: {SQL_SERVER_CONFIG['database']}")
    print(f"Драйвер: {SQL_SERVER_CONFIG['driver']}")
    print("=" * 50)
    
    # Тестируем подключение
    if test_connection():
        # Создаем базу данных
        if create_database():
            print("\n" + "=" * 50)
            print("✅ Готово! Теперь можно запускать бота.")
            print("Команда: python bot.py")
            print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("⚠️ Исправьте проблемы с подключением и запустите скрипт снова.")
        print("=" * 50)