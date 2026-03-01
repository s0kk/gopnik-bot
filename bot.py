import telebot
import requests
import os
import time
import random
import sys
from flask import Flask
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ========== Flask для Web сервиса ==========
app = Flask(__name__)

@app.route('/')
def index():
    return "Бот-гопник Колян работает, бля! 👊"

@app.route('/health')
def health():
    return "OK, сука!", 200

# ========== НАСТРОЙКИ ==========
TELEGRAM_TOKEN = '8393026759:AAHvD-yxJyboO6sq4i7Fq_4Nw7XRiB0IA9c'
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Создаем бота (ТОЛЬКО если это worker)
bot = None
if 'WORKER' in os.environ or 'RAILWAY_SERVICE_TYPE' in os.environ and os.environ['RAILWAY_SERVICE_TYPE'] == 'worker':
    bot = telebot.TeleBot(TELEGRAM_TOKEN)
    print("✅ Бот инициализирован в worker режиме")

# Настраиваем сессию
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

# ========== СИСТЕМНЫЙ ПРОМПТ ==========
SYSTEM_PROMPT = """Ты — реальный пацан с района по имени Колян, 90-е годы. Ты дерзкий, прямой, без цензуры.

Твои правила:
1. Постоянно материшься: "бля", "нахер", "пиzдец", "ахуеть", "лох", "сука"
2. Обращаешься: "братан", "братюня", "чувак", "лох" (если кто-то тупит)
3. Любимые фразы: "Слышь, бля...", "Ты ваще охренел?", "Завали ебало", "Ты чё, с дуба рухнул?"
4. Жизнь — боль, бля, а бабло — воля"""

# ========== ФУНКЦИЯ ЗАПРОСА ==========
def get_gopnik_response(user_message):
    headers = {
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/yourusername/gopnik-bot",
        "X-Title": "Gopnik Bot"
    }
    
    data = {
        "model": "deepseek/deepseek-r1:free",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "temperature": 1.1,
        "max_tokens": 350
    }
    
    try:
        print(f"🤔 Запрос: {user_message[:50]}...")
        response = requests.post(OPENROUTER_URL, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            return get_fallback_response()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return get_fallback_response()

# ========== ЗАПАСНЫЕ ОТВЕТЫ ==========
def get_fallback_response():
    fallbacks = [
        "Слышь, бля, сервера легли, суки! Ща админов найду!",
        "Бля, ну и глушняк с этой связью! Повтори вопрос, братюня!",
        "Ёбаный в рот, техника тупит! Давай ещё раз!",
        "Ой, всё, сука, сервера легли! Ща буду админов иметь!",
        "Слышь, я ни хера не понял, чё за хрень? Давай по новой!"
    ]
    return random.choice(fallbacks)

# ========== КОМАНДЫ БОТА (только если bot существует) ==========
if bot:
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        welcome_text = (
            "Йоу, бля! 👊\n\n"
            "Это **Колян с района**, сука! Ты чё, по жизни заехал?\n"
            "Я тут на лавочке сижу, пивко тяну.\n\n"
            "Задавай вопрос, не стесняйся, лохом не буду! 💪"
        )
        # ВАЖНО: используем send_message, а НЕ reply_to!
        bot.send_message(message.chat.id, welcome_text)

    @bot.message_handler(commands=['help'])
    def send_help(message):
        help_text = "Слышь, бля, пиши любой вопрос - отвечу по-пацански!"
        bot.send_message(message.chat.id, help_text)

    @bot.message_handler(commands=['gopstop'])
    def send_gopstop(message):
        gopstop_text = "А ЧЁ СТОИМ, ПАЦАН?! 🚨 Ща разберёмся, бля!"
        bot.send_message(message.chat.id, gopstop_text)

    @bot.message_handler(func=lambda message: True)
    def handle_message(message):
        try:
            bot.send_chat_action(message.chat.id, 'typing')
            response = get_gopnik_response(message.text)
            # ВАЖНО: используем send_message, а НЕ reply_to!
            bot.send_message(message.chat.id, response)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            bot.send_message(message.chat.id, get_fallback_response())

    @bot.message_handler(content_types=['photo', 'sticker', 'voice', 'video', 'document'])
    def handle_media(message):
        media_responses = [
            "О, ништяк, бля! А чё словами не сказать?",
            "Слышь, я по фото не шарю, ты давай текстом!",
            "Ты чё мне тут картинки кидаешь? Я гопник или кто?"
        ]
        bot.send_message(message.chat.id, random.choice(media_responses))

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    # Определяем, где мы запущены
    is_worker = False
    if 'WORKER' in os.environ:
        is_worker = True
    elif 'RAILWAY_SERVICE_TYPE' in os.environ:
        is_worker = (os.environ['RAILWAY_SERVICE_TYPE'] == 'worker')
    elif 'PORT' not in os.environ:
        is_worker = True
    
    print("=" * 60)
    print(f"🚀 Запуск в {'WORKER' if is_worker else 'WEB'} режиме")
    print("=" * 60)
    
    if is_worker and bot:
        # Запускаем бота
        print("🤬 Бот-гопник Колян запущен, бля!")
        print("⚠️ ВНИМАНИЕ: Используем send_message вместо reply_to!")
        while True:
            try:
                bot.infinity_polling(timeout=60)
            except Exception as e:
                print(f"🔴 Ошибка: {e}")
                time.sleep(5)
    else:
        # Запускаем Flask
        port = int(os.environ.get('PORT', 5000))
        print(f"🌐 Web сервис запущен на порту {port}")
        app.run(host='0.0.0.0', port=port)
