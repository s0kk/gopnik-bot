import telebot
import requests
import os
import time
import random
import sys
import google.generativeai as genai
from flask import Flask
from collections import deque

# ========== ЯДЕРНЫЙ СБРОС ВСЕХ СЕССИЙ ==========
TELEGRAM_TOKEN = '8393026759:AAHvD-yxJyboO6sq4i7Fq_4Nw7XRiB0IA9c'

print("💣 НАЧИНАЮ ЯДЕРНЫЙ СБРОС...")

# 1. Сбрасываем вебхук
r1 = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook")
print(f"deleteWebhook: {r1.status_code}")

# 2. Закрываем все активные сессии
r2 = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/close")
print(f"close: {r2.status_code}")

# 3. Получаем информацию о текущих подключениях
r3 = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo")
print(f"webhook info: {r3.json()}")

time.sleep(3)
print("💣 СБРОС ЗАВЕРШЁН\n")

# ========== ПРОВЕРКА GUNICORN ==========
if 'gunicorn' in sys.argv[0] or 'GUNICORN_CMD_ARGS' in os.environ:
    print("🚫 Запущен через gunicorn - только Flask")
    app = Flask(__name__)
    @app.route('/')
    def index(): return "Колян жив"
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
    sys.exit(0)

# ========== FLASK ==========
app = Flask(__name__)
@app.route('/')
def index(): return "Колян жив 👊"
@app.route('/health')
def health(): return "OK", 200

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
    text = "\n\nРанее говорили:\n"
    for role, msg in chat_history[chat_id]:
        text += f"{'Ты' if role=='assistant' else 'Чел'}: {msg}\n"
    return text

# ========== СОЗДАНИЕ БОТА ==========
bot = None
is_worker = False

if 'WORKER' in os.environ or os.environ.get('RAILWAY_SERVICE_TYPE') == 'worker':
    is_worker = True
    try:
        bot = telebot.TeleBot(TELEGRAM_TOKEN)
        print("✅ Бот создан")
        
        # Тест подключения
        bot.get_me()
        print("✅ Подключение работает")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

# ========== МОДЕЛЬ GEMINI ==========
if bot:
    model = genai.GenerativeModel("gemini-2.5-flash", generation_config=generation_config)

SYSTEM_PROMPT = "Ты гопник Колян. Матерись, дерзкий, но по делу. ЗАКАНЧИВАЙ ОТВЕТЫ."

# ========== ФУНКЦИЯ ОТВЕТА ==========
def get_gopnik_response(user_message, chat_id):
    if not bot or not model:
        return "Сервера легли, ща админов найду"
    
    try:
        add_to_history(chat_id, "user", user_message)
        history = get_history_prompt(chat_id)
        
        prompt = (
            f"{SYSTEM_PROMPT}\n"
            f"{history}\n"
            f"Чел: {user_message}\n"
            f"Колян: "
        )
        
        resp = model.generate_content(prompt)
        
        if resp and resp.text:
            reply = resp.text.strip()
            add_to_history(chat_id, "assistant", reply)
            return reply
        return "Ошибка, повтори"
    except:
        return "Техника тупит, давай ещё"

# ========== КОМАНДЫ ==========
if bot:
    @bot.message_handler(commands=['start'])
    def start(m):
        cid = m.chat.id
        if cid in chat_history:
            del chat_history[cid]
        bot.send_message(cid, "Йоу, бля! Колян на связи с памятью!")

    @bot.message_handler(func=lambda m: True)
    def handle(m):
        try:
            bot.send_chat_action(m.chat.id, 'typing')
            reply = get_gopnik_response(m.text, m.chat.id)
            bot.send_message(m.chat.id, reply)
        except:
            bot.send_message(m.chat.id, "Ошибка, брат")

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    print("="*50)
    print(f"Режим: {'WORKER' if is_worker else 'WEB'}")
    
    if is_worker and bot:
        print("🤬 Бот Колян запущен")
        while True:
            try:
                bot.infinity_polling()
            except Exception as e:
                print(f"Ошибка: {e}, перезапуск...")
                time.sleep(5)
    else:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
