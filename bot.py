import telebot
import requests
import os
import time
import random
import sys
import google.generativeai as genai
from flask import Flask
from collections import deque
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ========== ЖЁСТКАЯ ЗАЩИТА ОТ 409 ==========
TELEGRAM_TOKEN = '8393026759:AAHvD-yxJyboO6sq4i7Fq_4Nw7XRiB0IA9c'

# Сбрасываем все вебхуки и закрываем старые сессии
print("🔄 Сброс всех подключений Telegram...")
try:
    requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook")
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/close")
    print("✅ Старые подключения сброшены")
except:
    print("⚠️ Не удалось сбросить подключения")

time.sleep(2)  # Даем время на сброс

# ========== ЖЕСТЧАЙШАЯ ПРОВЕРКА ДЛЯ GUNICORN ==========
if 'gunicorn' in sys.argv[0] or 'GUNICORN_CMD_ARGS' in os.environ:
    print("🚫 Запущен через gunicorn - только Flask, бота НЕТ")
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return "Бот-гопник Колян работает! 👊"
    
    @app.route('/health')
    def health():
        return "OK", 200
    
    port = int(os.environ.get('PORT', 8080))
    print(f"🌐 Flask сервер запущен на порту {port}")
    app.run(host='0.0.0.0', port=port)
    sys.exit(0)

# ========== Flask для Web сервиса ==========
app = Flask(__name__)

@app.route('/')
def index():
    return "Бот-гопник Колян работает с Gemini! 👊"

@app.route('/health')
def health():
    return "OK, сука!", 200

# ========== НАСТРОЙКИ ==========
GEMINI_API_KEY = 'AIzaSyCZdIlCriIT78AVVhLfMIsICEahuvpRAYk'

# Настраиваем Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Настройки генерации
generation_config = {
    "temperature": 1.2,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 1500,
}

# ========== ПАМЯТЬ ДЛЯ КАЖДОГО ЧАТА ==========
chat_history = {}  # {chat_id: deque([(role, text), ...])}

def add_to_history(chat_id, role, text):
    """Добавляет сообщение в историю чата"""
    if chat_id not in chat_history:
        chat_history[chat_id] = deque(maxlen=10)
    chat_history[chat_id].append((role, text))

def get_history_prompt(chat_id):
    """Собирает историю в промпт"""
    if chat_id not in chat_history or len(chat_history[chat_id]) == 0:
        return ""
    
    history_text = "\n\nВот что мы обсуждали ранее:\n"
    for role, text in chat_history[chat_id]:
        if role == "user":
            history_text += f"Пользователь: {text}\n"
        else:
            history_text += f"Колян: {text}\n"
    
    return history_text

# ========== ДАЛЬШЕ ТВОЙ КОД С БОТОМ ==========
# ... (весь остальной код, который у тебя был)

# Создаем бота
bot = None
is_worker = False

if 'WORKER' in os.environ or ('RAILWAY_SERVICE_TYPE' in os.environ and os.environ['RAILWAY_SERVICE_TYPE'] == 'worker'):
    is_worker = True
    try:
        bot = telebot.TeleBot(TELEGRAM_TOKEN)
        print("✅ Бот инициализирован")
        
        # Сбрасываем вебхуки
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook")
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url=")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

# Создаем модель Gemini
if bot:
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=generation_config
        )
        print("✅ Модель Gemini создана")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        model = None

# ========== СИСТЕМНЫЙ ПРОМПТ ==========
SYSTEM_PROMPT = """Ты — реальный пацан с района по имени Колян, 90-е годы. Ты дерзкий, прямой, без цензуры.

Твои правила:
1. Постоянно материшься: "бля", "нахер", "пиzдец", "ахуеть", "лох", "сука"
2. Обращаешься: "братан", "братюня", "чувак", "лох"
3. Любимые фразы: "Слышь, бля...", "Ты ваще охренел?", "Завали ебало"
4. Жизнь — боль, бля, а бабло — воля

ВАЖНЕЙШИЕ ПРАВИЛА:
1. ТЫ ВСЕГДА ЗАКАНЧИВАЕШЬ МЫСЛЬ. НИКОГДА НЕ ОБРЫВАЕШЬ ОТВЕТ.
2. Ты даёшь ПОЛНЫЙ ответ. Если пишешь код — пиши ВЕСЬ код.
3. Ты ПОМНИШЬ предыдущие сообщения."""

# ========== ФУНКЦИЯ ЗАПРОСА ==========
def get_gopnik_response(user_message, chat_id):
    if not bot or not model:
        return get_fallback_response()

    try:
        print(f"🎉 Запуск: {user_message[:50]}...")

        add_to_history(chat_id, "user", user_message)
        history = get_history_prompt(chat_id)

        full_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"{history}\n\n"
            f"Сейчас тебя спросили: \"{user_message}\"\n\n"
            f"Твой ПОЛНЫЙ ответ (допиши до конца, сделай то что просят, используй историю если нужно): "
        )

        response = model.generate_content(full_prompt)

        if response and response.text:
            reply = response.text.strip()
            add_to_history(chat_id, "assistant", reply)
            print(f"🎉 Ответ получен")
            return reply
        else:
            return get_fallback_response()

    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        return get_fallback_response()
# ========== ЗАПАСНЫЕ ОТВЕТЫ ==========
def get_fallback_response():
    fallbacks = [
        "Слышь, бля, сервера легли, суки! Ща админов найду!",
        "Бля, ну и глушняк с этой связью! Повтори вопрос, братняк!",
        "Ёбаный в рот, техника тупит! Давай ещё раз!",
        "Ой, всё, сука, сервера легли! Ща буду админов иметь!"
    ]
    return random.choice(fallbacks)

# ========== КОМАНДЫ ==========
if bot:
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        chat_id = message.chat.id
        if chat_id in chat_history:
            del chat_history[chat_id]
        
        welcome_text = (
            "Йоу, бля! 👊\n\n"
            "Это **Колян с района**, сука! Я теперь с **ПАМЯТЬЮ**, всё помню, не тупи!\n\n"
            "Задавай вопрос, не стесняйся, лохом не буду! 💪"
        )
        bot.send_message(chat_id, welcome_text)
        add_to_history(chat_id, "assistant", welcome_text)

    @bot.message_handler(commands=['help'])
    def send_help(message):
        chat_id = message.chat.id
        help_text = (
            "Слышь, бля, чё непонятного?\n\n"
            "Пиши любой вопрос — отвечу по-пацански!\n"
            "/start — поздороваться\n"
            "/help — если ты даун\n"
            "/clear — очистить память\n"
            "/gopstop — если хочешь жёсткий ответ"
        )
        bot.send_message(chat_id, help_text)

    @bot.message_handler(commands=['clear'])
    def clear_history(message):
        chat_id = message.chat.id
        if chat_id in chat_history:
            del chat_history[chat_id]
        bot.send_message(chat_id, "Всё, бля, память очистил! Заново погнали! 👊")

    @bot.message_handler(commands=['gopstop'])
    def send_gopstop(message):
        chat_id = message.chat.id
        gopstop_text = (
            "**А ЧЁ СТОИМ, ПАЦАН?!** 🚨\n\n"
            "Ща разберёмся по понятиям, бля!\n"
            "Жизнь — боль, сука, а бабло — воля!\n"
            "Кто не скачет, тот лох, понял?!\n\n"
            "Ладно, расслабься, я пошутил. Чё спрашивать будешь?"
        )
        bot.send_message(chat_id, gopstop_text)

    @bot.message_handler(func=lambda message: True)
    def handle_message(message):
        try:
            chat_id = message.chat.id
            bot.send_chat_action(chat_id, 'typing')
            response = get_gopnik_response(message.text, chat_id)
            bot.send_message(chat_id, response)
        except Exception as e:
            print(f"❌ Ошибка в обработчике: {e}")
            bot.send_message(message.chat.id, get_fallback_response())

    @bot.message_handler(content_types=['photo', 'sticker', 'voice', 'video', 'document'])
    def handle_media(message):
        media_responses = [
            "О, ништяк, бля! А чё словами не сказать?",
            "Слышь, я по фото не шарю, ты давай текстом!",
            "Ты чё мне тут картинки кидаешь? Я гопник или фотограф?",
            "Семечки есть? Нет? А картинки кидаешь... Ну ладно, заценил."
        ]
        bot.send_message(message.chat.id, random.choice(media_responses))

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    print("=" * 60)
    print(f"🚀 Запуск в {'WORKER' if is_worker else 'WEB'} режиме")
    print("=" * 60)

    if is_worker and bot:
        print("🤬 Бот-гопник Колян с ПАМЯТЬЮ!")
        print(f"🔑 Gemini ключ: {GEMINI_API_KEY[:15]}...")
        print(f"📊 Память: 10 сообщений на чат")
        print(f"📝 Макс. токенов: 1500")

        while True:
            try:
                bot.infinity_polling(timeout=60, long_polling_timeout=60)
            except Exception as e:
                print(f"🔴 Ошибка бота: {e}")
                print("🟡 Перезапуск через 5 секунд, бля...")
                time.sleep(5)
    else:
        port = int(os.environ.get('PORT', 5000))
        print(f"🌐 Web сервис запущен на порту {port}")
        app.run(host='0.0.0.0', port=port)
