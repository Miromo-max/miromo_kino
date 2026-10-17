import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Tokeningiz
TOKEN = "8783824849:AAGE4BaxYlXTkvAAih6QL-lfSyNDayXoOXM"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- BAZANI SOZLASH (SQLite) ---
conn = sqlite3.connect("movies.db")
cursor = conn.cursor()

# 1. Kinolar jadvali
cursor.execute("""
CREATE TABLE IF NOT EXISTS movies (
    code TEXT PRIMARY KEY,
    file_id TEXT
)""")

# 2. Foydalanuvchilar tili uchun jadval
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    language TEXT
)""")
conn.commit()


# -------------------------------

# /start buyrug'i - Til tanlash tugmalari bilan
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")
        ]
    ])

    await message.answer(
        "👋 Assalomu alaykum / Здравствуйте!\n\n"
        "🎬 Miromo Kino botiga xush kelibsiz!\n"
        "Iltimos, tilni tanlang / Пожалуйста, выберите язык:",
        reply_markup=keyboard
    )


# Tugmalar bosilganda ishlaydigan qism (Callback query)
@dp.callback_query(F.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]  # 'uz' yoki 'ru'
    user_id = callback.from_user.id

    cursor.execute("INSERT OR REPLACE INTO users (user_id, language) VALUES (?, ?)", (user_id, lang))
    conn.commit()

    if lang == "uz":
        await callback.message.edit_text(
            "✅ Til o'zbek tiliga o'zgartirildi!\n\n"
            "🔍 Kino ko'rish uchun uning kodini yuboring (Masalan: 101):"
        )
    else:
        await callback.message.edit_text(
            "✅ Язык изменен на русский!\n\n"
            "🔍 Для просмотра фильма отправьте его код (Например: 101):"
        )
    await callback.answer()


# Kino kodini yuborganda videoni topib berish
@dp.message(F.text)
async def get_movie_by_code(message: types.Message):
    code = message.text.strip()
    user_id = message.from_user.id

    cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    user_lang = cursor.fetchone()
    lang = user_lang[0] if user_lang else "uz"

    cursor.execute("SELECT file_id FROM movies WHERE code = ?", (code,))
    result = cursor.fetchone()

    if result:
        file_id = result[0]
        caption = (
            f"🍿 Kino kodi: {code}\n✨ Maroqli hordiq tilaymiz!"
            if lang == "uz"
            else f"🍿 Код фильма: {code}\n✨ Приятного просмотра!"
        )
        await message.answer_video(video=file_id, caption=caption)
    else:
        error_msg = (
            "❌ Bu kod bo'yicha kino topilmadi."
            if lang == "uz"
            else "❌ По этому коду фильм не найден."
        )
        await message.answer(error_msg)


# Botga video yuborsangiz, uning file_id sini chiqarib beradi
@dp.message(F.video)
async def get_video_file_id(message: types.Message):
    file_id = message.video.file_id
    await message.answer(
        f"✅ Ushbu videoning File ID si:\n\n`{file_id}`\n\n"
        "Bu kodni nusxalab, kinoga kod berib bazaga saqlaysiz!",
        parse_mode="Markdown"
    )


# Botni ishga tushirish
async def main():
    logging.basicConfig(level=logging.INFO)
    print("🚀 Bot ishga tushmoqda...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        print(f"Webook'ni o'chirishda ogohlantirish (muammo emas): {e}")

    print("🚀 Bot muvaffaqiyatli ishga tushdi va til tanlash qo'shildi!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())