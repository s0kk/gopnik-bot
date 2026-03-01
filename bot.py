import telebot
import requests
import os
import time
import random
import sys
import google.generativeai as genai
from flask import Flask
from collections import deque

# ========== ЯДЕРНЫЙ СБРОС ==========
TELEGRAM_TOKEN = '8393026759:AAHvD-yxJyboO6sq4i7Fq_4Nw7XRiB0IA9c'

print("💣 СБРОС...")
requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook")
requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/close")
time.sleep(2)

# ========== ПРОВЕРКА GUNICORN ==========
if 'gunicorn' in sys.argv[0] or 'GUNICORN_CMD_ARGS' in os.environ:
    app = Flask(__name__)
    @app.route('/')
    def index(): return "Колян жив"
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
    sys.exit(0)

app = Flask(__name__)
@app.route('/')
def index(): return "Колян жив 👊"

# ========== GEMINI ==========
GEMINI_API_KEY = 'AIzaSyCZdIlCriIT78AVVhLfMIsICEahuvpRAYk'
genai.configure(api_key=GEMINI_API_KEY)

generation_config = {
    "temperature": 1.2,
    "max_output_tokens": 1500,
}

# ========== ПАМЯТЬ ==========
chat_history = {}

def add_to_history(chat_id, role, text):
    if chat_id not in chat_history:
        chat_history[chat_id] = deque(maxlen=10)
    chat_history[chat_id].append((role, text))

def get_history_prompt(chat_id):
    if chat_id not in chat_history:
        return ""
    text = "\nРанее:\n"
    for role, msg in chat_history[chat_id]:
        text += f"{'Колян' if role=='assistant' else 'Ты'}: {msg}\n"
    return text

# ========== БОТ ==========
bot = None
is_worker = os.environ.get('WORKER') == 'true' or os.environ.get('RAILWAY_SERVICE_TYPE') == 'worker'

if is_worker:
    bot = telebot.TeleBot(TELEGRAM_TOKEN)
    print("✅ Бот создан")

SYSTEM_PROMPT = "Ты гопник Колян. Матерись, но помогай. ЗАКАНЧИВАЙ ОТВЕТЫ ПОЛНОСТЬЮ."

# ========== ФУНКЦИЯ ОТВЕТА ==========
def get_gopnik_response(user_message, chat_id):
    if not bot:
        return "Ошибка бота"
    
    try:
        add_to_history(chat_id, "user", user_message)
        history = get_history_prompt(chat_id)
        
        prompt = f"{SYSTEM_PROMPT}\n{history}\nЧел: {user_message}\nКолян:"
        
        # Пробуем разные модели
        models = [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-pro",
        ]
        
        for model_name in models:
            try:
                model = genai.GenerativeModel(model_name, generation_config=generation_config)
                resp = model.generate_content(prompt, timeout=10)
                if resp and resp.text:
                    reply = resp.text.strip()
                    add_to_history(chat_id, "assistant", reply)
                    return reply
            except:
                continue
        
        return "Техника тупит, давай ещё раз"
    except Exception as e:
        print(f"Ошибка: {e}")
        return "Техника тупит, давай ещё"

# ========== КОМАНДЫ ==========
if bot:
    @bot.message_handler(commands=['start'])
    def start(m):
        cid = m.chat.id
        chat_history.pop(cid, None)
        bot.send_message(cid, "Йоу, бля! Колян на связи с памятью!")

    @bot.message_handler(func=lambda m: True)
    def handle(m):
        bot.send_chat_action(m.chat.id, 'typing')
        reply = get_gopnik_response(m.text, m.chat.id)
        bot.send_message(m.chat.id, reply)

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    if is_worker and bot:
        print("🤬 Колян запущен")
        bot.infinity_polling()
    else:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
