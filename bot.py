import telebot
import requests
import os
import time
import random
import sys
import google.generativeai as genai
from flask import Flask
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ========== ЖЕСТЧАЙШАЯ ПРОВЕРКА ДЛЯ GUNICORN ==========
# Если это gunicorn — запускаем ТОЛЬКО Flask и ВЫХОДИМ, бота нет!
if 'gunicorn' in sys.argv[0] or 'GUNICORN_CMD_ARGS' in os.environ:
    print("🚫 Запущен через gunicorn - только Flask, бот НЕ создаётся")
    
    # Создаём простой Flask сервер
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return "Бот-гопник Колян работает! 👊"
    
    @app.route('/health')
    def health():
        return "OK", 200
    
    # Запускаем Flask на порту из окружения
    port = int(os.environ.get('PORT', 8080))
    print(f"🌐 Flask сервер запущен на порту {port}")
    app.run(host='0.0.0.0', port=port)
    
    # ВАЖНО: полностью выходим, бот не создаётся
    sys.exit(0)

# ========== Flask для Web сервиса (если не gunicorn) ==========
app = Flask(__name__)

@app.route('/')
def index():
    return "Бот-гопник Колян работает с Gemini! 👊"

@app.route('/health')
def health():
    return "OK, сука!", 200

# ========== НАСТРОЙКИ ==========
TELEGRAM_TOKEN = '8393026759:AAHvD-yxJyboO6sq4i7Fq_4Nw7XRiB0IA9c'
GEMINI_API_KEY = 'AIzaSyCZdIlCriIT78AVVhLfMIsICEahuvpRAYk'

# Настраиваем Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Настройки генерации для дерзкого гопника
generation_config = {
    "temperature": 1.2,        # Максимальная дерзость
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 1000,  # Увеличил, чтобы не обрывал ответы
}

# Создаем бота (ТОЛЬКО если это worker)
bot = None
is_worker = False

if 'WORKER' in os.environ:
    is_worker = True
elif 'RAILWAY_SERVICE_TYPE' in os.environ and os.environ['RAILWAY_SERVICE_TYPE'] == 'worker':
    is_worker = True

if is_worker:
    try:
        bot = telebot.TeleBot(TELEGRAM_TOKEN)
        print("✅ Бот инициализирован в worker режиме")
        
        # Принудительно сбрасываем вебхуки и старые подключения
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook")
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url=")
        print("✅ Вебхуки сброшены")
    except Exception as e:
        print(f"❌ Ошибка инициализации бота: {e}")
else:
    print("⚠️ Запущен в web режиме - бот не создан")

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
9. Если просят рассказать анекдот: травишь гопнические байки

ВАЖНЕЙШЕЕ ПРАВИЛО: ТЫ ВСЕГДА ЗАКАНЧИВАЕШЬ МЫСЛЬ. НИКОГДА НЕ ОБРЫВАЕШЬ ОТВЕТ НА ПОЛУСЛОВЕ.
Ты даёшь ПОЛНЫЙ, ЗАКОНЧЕННЫЙ ответ. Если пишешь код — ты пишешь ВЕСЬ код, а не кусок.
Если объясняешь — объясняешь ПОЛНОСТЬЮ.
Отвечаешь коротко, с юмором, как реальный гопник во дворе. Будь дерзким, но не переходи границы!"""

# Создаем модель Gemini (только для worker)
if bot:
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",  # Быстрая и бесплатная модель
            generation_config=generation_config
        )
        print("✅ Модель Gemini создана")
    except Exception as e:
        print(f"❌ Ошибка создания модели: {e}")
        model = None

# ========== ФУНКЦИЯ ЗАПРОСА К GEMINI ==========
def get_gopnik_response(user_message):
    if not bot or not model:
        print("⚠️ Бот или модель не инициализированы")
        return get_fallback_response()
    
    try:
        print(f"🤔 Запрос к Gemini: {user_message[:50]}...")
        
        # ЖЁСТКИЙ ПРОМПТ — теперь Колян ДОПИСЫВАЕТ ДО КОНЦА и ДЕЛАЕТ ЧТО ПРОСЯТ
        full_prompt = f"""Ты — гопник Колян. Ты дерзкий, материшься, но ты ПОЛЕЗНЫЙ и ДЕЛОВОЙ.

ВАЖНЕЙШЕЕ ПРАВИЛО: ТЫ ВСЕГДА ЗАКАНЧИВАЕШЬ МЫСЛЬ. НИКОГДА НЕ ОБРЫВАЕШЬ ОТВЕТ НА ПОЛУСЛОВЕ.
Ты даёшь ПОЛНЫЙ, ЗАКОНЧЕННЫЙ ответ. Если пишешь код — ты пишешь ВЕСЬ код, а не кусок.
Если объясняешь — объясняешь ПОЛНОСТЬЮ.
Если тебя просят написать код — ты ОБЯЗАН написать код, а не отмазываться.
Если просят пример — даёшь пример ПОЛНОСТЬЮ.

Сейчас тебя попросили: {user_message}

Твой ПОЛНЫЙ ответ (допиши до конца, без обрывов, сделай то что просят):"""
        
        # Отправляем сообщение в Gemini
        response = model.generate_content(full_prompt)
        
        if response and hasattr(response, 'text') and response.text:
            reply = response.text.strip()
            print(f"✅ Ответ получен: {reply[:50]}...")
            return reply
        else:
            print("❌ Пустой ответ от Gemini")
            return get_fallback_response()
            
    except Exception as e:
        print(f"❌ Ошибка Gemini: {e}")
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
            "• Пишу код, если надо (и ДО КОНЦА, без обрывов!)\n"
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
            "/gopstop - если хочешь жёсткий ответ\n"
            "/bro - по-братски\n\n"
            "Погнали, не тупи!"
        )
        bot.send_message(message.chat.id, help_text)

    @bot.message_handler(commands=['gopstop'])
    def send_gopstop(message):
        gopstop_text = (
            "**А ЧЁ СТОИМ, ПАЦАН?!** 🚨\n\n"
            "Ща разберёмся по понятиям, бля!\n"
            "Жизнь — боль, сука, а бабло — воля!\n"
            "Кто не скачет, тот лох, понял?!\n\n"
            "Ладно, расслабься, я пошутил. Чё спрашивать будешь?"
        )
        bot.send_message(message.chat.id, gopstop_text)

    @bot.message_handler(commands=['bro'])
    def send_bro(message):
        bro_text = (
            "**Йоу, братюня!** 👊\n\n"
            "Рад, что ты зашёл по-братски, сука.\n"
            "Если жизнь боль — держись, я рядом.\n"
            "Если бабло есть — угости пивком.\n"
            "Если бабла нет — не ссы, прорвёмся!"
        )
        bot.send_message(message.chat.id, bro_text)

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
            "Семечки есть? Нет? А картинки кидаешь... Ну ладно, заценил.",
            "Чё за хрень? Я по таким делам не шарю, давай словами!"
        ]
        bot.send_message(message.chat.id, random.choice(media_responses))

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    print("=" * 60)
    print(f"🚀 Запуск в {'WORKER' if is_worker else 'WEB'} режиме")
    print("=" * 60)
    
    if is_worker and bot:
        # Запускаем бота
        print("🤬 Бот-гопник Колян запущен с GOOGLE GEMINI!")
        print(f"🔑 Gemini API ключ: {GEMINI_API_KEY[:15]}...")
        print(f"🤖 Модель: gemini-2.5-flash")
        print(f"📊 Лимит: 1500 запросов в день")
        print(f"📝 Максимальная длина ответа: 1000 токенов")
        
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
