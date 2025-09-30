import psycopg2
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "host": os.getenv("DB_HOST", "localhost"),
}

# SQL для создания таблиц
SQL_SCRIPT = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY NOT NULL,
    username VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS user_words (
    word_id SERIAL PRIMARY KEY,
    word_ru VARCHAR(30) NOT NULL,
    word_en VARCHAR(30) NOT NULL,
    user_id INTEGER REFERENCES users(telegram_id) NOT NULL
);

CREATE TABLE IF NOT EXISTS words (
    word_id SERIAL PRIMARY KEY,
    word_ru VARCHAR(30) NOT NULL,
    word_en VARCHAR(30) NOT NULL
);
"""

def init_db():
    try:
        # Контекстный менеджер автоматически закрывает соединение
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(SQL_SCRIPT)
                conn.commit()
        print("✅ Таблицы успешно созданы или уже существуют.")

    except Exception as e:
        print("❌ Ошибка при создании таблиц:", e)

if __name__ == "__main__":
    init_db()
