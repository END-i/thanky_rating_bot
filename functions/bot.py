import asyncio
import sqlite3
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, MessageReactionUpdated
from aiohttp import web

BOT_TOKEN = os.getenv("8809668157:AAFLcMLEAOin-l0yLygDlfeViTiHLeWKUbk")
DB_FILE = "rating.db"

POSITIVE_WORDS = {
    "дякую", "спасибо", "thank you", "thanks", "дяка", 
    "спасибули", "спасибі", "спс", "thx", "ty", "danke"
}
POSITIVE_EMOJIS = {"👍", "❤️", "🔥", "🥰", "👏", "🤝", "💯", "🫶", "💖", "🤍"}

MESSAGES = {
    "uk": "Користувач {name} отримав +1 до рейтингу.\nЗагальний рейтинг: {rating}",
    "en": "User {name} received +1 rating.\nTotal rating: {rating}"
}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                rating INTEGER DEFAULT 0
            )
        """)

def add_rating(user_id: int, username: str) -> int:
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username, rating) VALUES (?, ?, 0)", (user_id, username))
        cursor.execute("UPDATE users SET rating = rating + 1, username = ? WHERE user_id = ?", (username, user_id))
        cursor.execute("SELECT rating FROM users WHERE user_id = ?", (user_id,))
        return cursor.fetchone()[0]

def get_language(user_lang_code: str) -> str:
    return "uk" if user_lang_code in ["uk", "ru"] else "en"

@dp.message(F.reply_to_message)
async def handle_reply(message: Message):
    if message.from_user.id == message.reply_to_message.from_user.id:
        return 

    text = message.text.lower() if message.text else ""
    
    has_trigger = any(word in text for word in POSITIVE_WORDS) or any(emoji in text for emoji in POSITIVE_EMOJIS)
    
    if has_trigger:
        target_user = message.reply_to_message.from_user
        username = target_user.username or target_user.first_name
        new_rating = add_rating(target_user.id, username)
        
        lang = get_language(message.from_user.language_code)
        response = MESSAGES[lang].format(name=username, rating=new_rating)
        await message.answer(response)

@dp.message_reaction()
async def handle_reaction(reaction: MessageReactionUpdated):
    if reaction.actor_chat or not reaction.new:
        return
        
    for current_reaction in reaction.new:
        if current_reaction.type == "emoji" and current_reaction.emoji in POSITIVE_EMOJIS:
            pass

async def handle(request):
    return web.Response(text="Bot is running")

async def main():
    init_db()
    
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
