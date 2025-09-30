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

# Данные для вставки
WORDS = [
    ("красный", "red"),
    ("синий", "blue"),
    ("зелёный", "green"),
    ("жёлтый", "yellow"),
    ("чёрный", "black"),

    ("я", "I"),
    ("ты", "you"),
    ("он", "he"),
    ("она", "she"),
    ("мы", "we"),

    ("кошка", "cat"),
    ("собака", "dog"),
    ("птица", "bird"),
    ("рыба", "fish"),
    ("лошадь", "horse"),

    ("дом", "house"),
    ("книга", "book"),
    ("стол", "table"),
    ("стул", "chair"),
    ("телефон", "phone"),
]

def insert_words():
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.executemany(
                    "INSERT INTO words (word_ru, word_en) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                    WORDS
                )
                conn.commit()
        print("✅ Слова успешно добавлены в таблицу `words`.")
    except Exception as e:
        print("❌ Ошибка при вставке слов:", e)

if __name__ == "__main__":
    insert_words()
