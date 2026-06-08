import logging
import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from groq import Groq

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_API_KEY = GROQ_API_KEY.encode("ascii", errors="ignore").decode("ascii")
GROQ_MODEL = "llama-3.3-70b-versatile"
SYSTEM_PROMPT = "You are a friendly and smart assistant. Always reply in Persian (Farsi). Keep answers very short and friendly."

logging.basicConfig(level=logging.INFO)

groq_client = Groq(api_key=GROQ_API_KEY)

history = {}

def get_reply(user_id, text):
    if user_id not in history:
        history[user_id] = []
    history[user_id].append({"role": "user", "content": text})
    if len(history[user_id]) > 20:
        history[user_id] = history[user_id][-20:]
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history[user_id],
        max_tokens=300,
    )
    reply = response.choices[0].message.content.strip()
    history[user_id].append({"role": "assistant", "content": reply})
    return reply

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return
    chat_type = message.chat.type
    text = message.text
    bot_username = context.bot.username
    if chat_type == "private":
        pass
    elif chat_type in ("group", "supergroup"):
        mentioned = f"@{bot_username}" in text
        replied = message.reply_to_message and message.reply_to_message.from_user.username == bot_username
        if not mentioned and not replied:
            return
        text = text.replace(f"@{bot_username}", "").strip()
    else:
        return
    try:
        await context.bot.send_chat_action(chat_id=message.chat_id, action="typing")
        reply = get_reply(message.from_user.id, text)
        await message.reply_text(reply)
    except Exception as e:
        logging.error(f"Error: {e}")
        await message.reply_text("متاسفم، مشکلی پیش آمد.")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
