import telebot
import requests
import os
import time
import random
import sys
import google.generativeai as genai
from flask import Flask
from collections import deque

# ========== НОВЫЙ ТОКЕН ==========
TELEGRAM_TOKEN = '8783129328:AAE-A75nPcaOXjx_S0kx_wEbf5cCz80yO5I'

# ========== ЖЁСТКОЕ УБИЙСТВО ВСЕХ ПОДКЛЮЧЕНИЙ ==========
print("💀 ТОТАЛЬНОЕ УБИЙСТВО ВСЕХ ПОДКЛЮЧЕНИЙ...")

# Сначала закрываем всё
requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook")
requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/close")
time.sleep(2)

# ========== ПРОВЕРКА НА ДРУГИЕ ИНСТАНСЫ ==========
# Проверяем, не запущен ли бот где-то ещё
try:
    info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo").json()
    print(f"📊 Инфо: {info}")
except:
    pass

# ========== ПРОВЕРКА GUNICORN ==========
if 'gunicorn' in sys.argv[0]:
    print("🚫 Запущен через gunicorn - выход")
    sys.exit(0)

# ========== FLASK ==========
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

# ========== БОТ ==========
print("🤖 СОЗДАНИЕ БОТА...")
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Проверяем подключение
try:
    me = bot.get_me()
    print(f"✅ БОТ: @{me.username}")
except Exception as e:
    print(f"❌ Ошибка: {e}")

SYSTEM_PROMPT = """Ты — гопник Колян. Отвечаешь дерзко, с матом, но по делу.

ПРАВИЛА:
1. Матерись, но не переходи границы
2. Отвечай ПОЛНОСТЬЮ, не обрывай на полуслове
3. Если просят код — пиши код
4. Используй слова: бля, сука, нахер, братан"""

# ========== ФУНКЦИЯ ОТВЕТА ==========
def get_gopnik_response(user_message):
    try:
        prompt = f"""{SYSTEM_PROMPT}

Чел: {user_message}
Колян (ответь полностью):"""
        
        # Пробуем модели
        models = ["gemini-1.5-flash", "gemini-pro"]
        
        for model_name in models:
            try:
                print(f"🔄 Пробую {model_name}...")
                model = genai.GenerativeModel(model_name, generation_config=generation_config)
                resp = model.generate_content(prompt)
                
                if resp and resp.text:
                    reply = resp.text.strip()
                    print(f"✅ Ответ получен")
                    return reply
            except Exception as e:
                print(f"❌ {model_name}: {e}")
                continue
        
        return "Техника тупит, бля. Повтори вопрос."
        
    except Exception as e:
        print(f"💥 Ошибка: {e}")
        return "Ошибка, сорян."

# ========== КОМАНДЫ ==========
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Йоу, бля! 👊\n\n"
        "Я **Колян**!\n"
        "Спрашивай что хочешь."
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        reply = get_gopnik_response(message.text)
        bot.send_message(message.chat.id, reply)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        bot.send_message(message.chat.id, "Ошибка, братан.")

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    print("=" * 50)
    print("🤬 КОЛЯН ЗАПУЩЕН")
    print("=" * 50)
    
    while True:
        try:
            bot.infinity_polling()
        except Exception as e:
            print(f"⚠️ Ошибка: {e}, перезапуск...")
            time.sleep(5)
