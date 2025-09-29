import asyncio
import asyncpg
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from googletrans import Translator
import random
import os
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

DB_CONFIG = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "database": os.getenv("DB_NAME"),
    "host": os.getenv("DB_HOST"),
}
API_TOKEN = os.getenv("BOT_TOKEN")

# создаём объекты
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
translator = Translator()

# Состояния
class AddWord(StatesGroup):
    waiting_for_word = State()

class DeleteWord(StatesGroup):
    waiting_for_word = State()

# создаём пул соединений
pool: asyncpg.Pool = None

async def queries_bd(query: str, *params):
    """
    Универсальная функция для SQL-запросов.
    """
    async with pool.acquire() as conn:
        query_type = query.strip().split()[0].upper()
        if query_type == "SELECT":
            return await conn.fetch(query, *params)
        else:  # INSERT, DELETE, UPDATE
            result = await conn.execute(query, *params)
            return int(result.split()[-1])  # кол-во изменённых строк

async def set_commands():
    commands = [
        types.BotCommand(command="/add", description="Добавить слово"),
        types.BotCommand(command="/delete", description="Удалить слово"),
        types.BotCommand(command="/list_words", description="Список слов"),
    ]
    await bot.set_my_commands(commands)

# ---------- Клавиатуры ----------
def start_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Поехали!", callback_data="go")
    return kb.as_markup()

def next_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Дальше ➡️", callback_data="go")
    return kb.as_markup()

def options_keyboard(options, correct):
    kb = InlineKeyboardBuilder()
    for opt in options:
        kb.button(text=opt, callback_data=f"{opt}_{correct}")
    kb.adjust(2)
    return kb.as_markup()

# ---------- Хендлеры ----------
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await queries_bd(
        """INSERT INTO users(telegram_id, username) VALUES($1, $2)
           ON CONFLICT (telegram_id) DO NOTHING;""",
        message.from_user.id, message.from_user.username
    )
    await message.answer(
        "Привет 👋\n"
        "Давай потренируемся в английском!\n\n"
        "Ты можешь собирать свою базу для обучения:\n\n"
        "➕ Добавить слово\n"
        "🔙 Удалить слово\n\n"
        "Ну что, поехали? ⬇️",
        reply_markup=start_keyboard()
    )

@dp.message(Command("add"))
async def cmd_add(message: types.Message, state: FSMContext):
    await message.answer("Введите слово, которое хотите добавить ✍️")
    await state.set_state(AddWord.waiting_for_word)

@dp.message(Command("delete"))
async def cmd_delete(message: types.Message, state: FSMContext):
    await message.answer("Введите слово, которое хотите удалить ✍️")
    await state.set_state(DeleteWord.waiting_for_word)

@dp.message(Command("list_words"))
async def cmd_list_words(message: types.Message):
    rows = await queries_bd(
        """SELECT word_ru, word_en FROM user_words WHERE user_id = $1""",
        message.from_user.id
    )
    if rows:
        words = [f"{r['word_ru']} - {r['word_en']}" for r in rows]
        await message.answer("\n".join(words))
    else:
        await message.answer("У вас нет добавленных слов")

# ---------- Callback ----------
@dp.callback_query()
async def random_word(callback: types.CallbackQuery):
    if callback.data == "go":
        user_id = callback.from_user.id
        query = await queries_bd(
            """SELECT word_ru, word_en
               FROM (
                    SELECT word_ru, word_en FROM user_words WHERE user_id = $1
                    UNION
                    SELECT word_ru, word_en FROM words
               ) AS combined
               ORDER BY RANDOM() LIMIT 1;""",
            user_id
        )
        word_en = query[0]["word_en"]
        word_ru = query[0]["word_ru"]

        distractors = await queries_bd(
            """SELECT word_en
               FROM (
                    SELECT word_en FROM user_words WHERE user_id = $1
                    UNION
                    SELECT word_en FROM words
               ) AS combined
               WHERE word_en != $2
               ORDER BY RANDOM() LIMIT 3;""",
            user_id, word_en
        )
        options = [d["word_en"] for d in distractors] + [word_en]
        random.shuffle(options)

        await callback.message.answer(
            f"Как переводится слово: {word_ru}",
            reply_markup=options_keyboard(options, word_en)
        )
    else:
        try:
            chosen, correct = callback.data.split("_")
            if chosen == correct:
                await callback.message.answer("Совершенно верно! 🎉", reply_markup=next_keyboard())
            else:
                await callback.message.answer("Неверно ❌")
        except Exception as e:
            print("Ошибка при проверке:", e)

    await callback.answer()

# ---------- FSM ----------
@dp.message(AddWord.waiting_for_word)
async def add_word(message: types.Message, state: FSMContext):
    word_ru = message.text.strip().capitalize()
    word_en = translator.translate(word_ru, src="ru", dest="en").text
    await queries_bd(
        "INSERT INTO user_words(word_ru, word_en, user_id) VALUES($1, $2, $3);",
        word_ru, word_en, message.from_user.id
    )
    await message.answer(f"✅ Слово '{word_ru}: {word_en}' добавлено!")
    await state.clear()

@dp.message(DeleteWord.waiting_for_word)
async def delete_word(message: types.Message, state: FSMContext):
    result = await queries_bd(
        "DELETE FROM user_words WHERE word_ru = $1 and user_id = $2;",
        message.text.strip(), message.from_user.id
    )
    if result == 1:
        await message.answer(f"✅ Слово '{message.text}' удалено!")
    else:
        await message.answer(f"❌ Слово '{message.text}' не найдено!")
    await state.clear()

# ---------- Main ----------
async def main():
    global pool
    pool = await asyncpg.create_pool(**DB_CONFIG)  # создаём пул
    await set_commands()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
