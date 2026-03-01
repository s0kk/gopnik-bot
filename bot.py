import telebot
import requests
import os
import time
import random
import sys
from flask import Flask
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ========== ЖЕСТКАЯ ПРОВЕРКА ДЛЯ GUNICORN ==========
if 'gunicorn' in sys.argv[0] or 'GUNICORN_CMD_ARGS' in os.environ:
    print("🚫 Запущен через gunicorn - бот не инициализируется")
    # Запускаем только Flask
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return "Бот-гопник Колян работает, бля! 👊"
    
    @app.route('/health')
    def health():
        return "OK, сука!", 200
    
    port = int(os.environ.get('PORT', 8081))
    print(f"🌐 Web сервис запущен на порту {port}")
    app.run(host='0.0.0.0', port=port)
    sys.exit(0)

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
OPENROUTER_API_KEY = "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"

# Создаем бота (ТОЛЬКО если это worker)
bot = None
if 'WORKER' in os.environ or ('RAILWAY_SERVICE_TYPE' in os.environ and os.environ['RAILWAY_SERVICE_TYPE'] == 'worker'):
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
4. Жизнь — боль, бля, а бабло — воля
5. Если чё-то сломалось: "Пиzдец, сервера легли, суки! Ща админам наваляю"
6. На тупые вопросы: "Ты чё, бля, самый умный? Я гопник или профессор?"
7. Про любовь: "Любовь это когда за неё морду готов бить, понял, бля?" 
8. Про работу: "Работа? Ты чё, попутал? Я крышую ларёк с семечками"

Отвечай коротко, с юмором, как реальный гопник во дворе. Будь дерзким, но не переходи границы!"""

# ========== ФУНКЦИЯ ЗАПРОСА К OPENROUTER ==========
def get_gopnik_response(user_message):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
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
        "max_tokens": 500
    }
    
    try:
        print(f"🤔 Запрос к OpenRouter: {user_message[:50]}...")
        response = requests.post(OPENROUTER_URL, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            reply = result['choices'][0]['message']['content']
            print(f"✅ Ответ получен: {reply[:50]}...")
            return reply
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"Ответ: {response.text}")
            return get_fallback_response()
    except Exception as e:
        print(f"❌ Ошибка при запросе: {e}")
        return get_fallback_response()

# ========== ЗАПАСНЫЕ ОТВЕТЫ ==========
def get_fallback_response():
    fallbacks = [
        "Слышь, бля, сервера легли, суки! Ща админов найду!",
        "Бля, ну и глушняк с этой связью! Повтори вопрос, братюня!",
        "Ёбаный в рот, техника тупит! Давай ещё раз!",
        "Ой, всё, сука, сервера легли! Ща буду админов иметь!",
        "Слышь, я ни хера не понял, чё за хрень? Давай по новой!",
        "Пиzдец, интернет лагает как бабки на рынке! Повтори!",
        "Ты чё, с дуба рухнул? Я тебя не слышу ваще! Пиши ещё раз!"
    ]
    return random.choice(fallbacks)

# ========== КОМАНДЫ БОТА ==========
if bot:
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        welcome_text = (
            "Йоу, бля! 👊\n\n"
            "Это **Колян с района**, сука! Ты чё, по жизни заехал?\n"
            "Я тут на лавочке сижу, пивко тяну, семечки щелкаю.\n\n"
            "**Чё умею:**\n"
            "• Отвечаю на вопросы по-пацански\n"
            "• Рассказываю жизненные истории\n"
            "• Даю советы, как настоящий братан\n\n"
            "Задавай вопрос, не стесняйся, лохом не буду! 💪"
        )
        bot.send_message(message.chat.id, welcome_text)

    @bot.message_handler(commands=['help'])
    def send_help(message):
        help_text = (
            "Слышь, бля, чё непонятного?\n\n"
            "Пиши любой вопрос - отвечу по-пацански!\n"
            "/start - поздороваться\n"
            "/help - если ты даун\n"
            "/gopstop - если хочешь жёсткий ответ"
        )
        bot.send_message(message.chat.id, help_text)

    @bot.message_handler(commands=['gopstop'])
    def send_gopstop(message):
        gopstop_text = (
            "**А ЧЁ СТОИМ, ПАЦАН?!** 🚨\n\n"
            "Ща разберёмся по понятиям, бля!\n"
            "Жизнь — боль, сука, а бабло — воля!\n"
            "Кто не скачет, тот лох, понял?!"
        )
        bot.send_message(message.chat.id, gopstop_text)

    @bot.message_handler(func=lambda message: True)
    def handle_message(message):
        try:
            bot.send_chat_action(message.chat.id, 'typing')
            response = get_gopnik_response(message.text)
            bot.send_message(message.chat.id, response)
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
    # Определяем, где мы запущены
    is_worker = False
    if 'WORKER' in os.environ:
        is_worker = True
    elif 'RAILWAY_SERVICE_TYPE' in os.environ:
        is_worker = (os.environ['RAILWAY_SERVICE_TYPE'] == 'worker')
    
    print("=" * 60)
    print(f"🚀 Запуск в {'WORKER' if is_worker else 'WEB'} режиме")
    print("=" * 60)
    
    if is_worker and bot:
        # Запускаем бота
        print("🤬 Бот-гопник Колян запущен, бля!")
        print(f"🔑 OpenRouter API ключ: {OPENROUTER_API_KEY[:15]}...")
        while True:
            try:
                bot.infinity_polling(timeout=60, long_polling_timeout=60)
            except Exception as e:
                print(f"🔴 Ошибка бота: {e}")
                print("🟡 Перезапуск через 5 секунд, бля...")
                time.sleep(5)
    else:
        # Запускаем Flask
        port = int(os.environ.get('PORT', 5000))
        print(f"🌐 Web сервис запущен на порту {port}")
        app.run(host='0.0.0.0', port=port)
