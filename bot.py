import telebot
import requests
import os
import threading
import time
import random
from flask import Flask
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ========== FLASK ДЛЯ RENDER ==========
app = Flask(__name__)

@app.route('/')
def index():
    return "Бот-гопник Колян работает! 👊"

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

# ========== НАСТРОЙКИ БОТА ==========
# Telegram токен (ваш)
TELEGRAM_TOKEN = '8393026759:AAHvD-yxJyboO6sq4i7Fq_4Nw7XRiB0IA9c'

# DeepSeek API ключ (из переменных окружения)
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')

if not DEEPSEEK_API_KEY:
    print("ОШИБКА: Не найден DEEPSEEK_API_KEY в переменных окружения!")
    # Для теста можно вставить напрямую, но лучше использовать переменные окружения
    # DEEPSEEK_API_KEY = 'sk-02a2e3e2f1a045dea571c4f3ac9cb33f'

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

# Создаем бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Настраиваем сессию с повторными попытками
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

# ========== СИСТЕМНЫЙ ПРОМПТ ДЛЯ ГОПНИКА ==========
SYSTEM_PROMPT = """Ты — типичный гопник из 90-х по имени Колян. Отвечаешь на всё с характерным пацанским акцентом, используешь сленг, но без откровенной грубости.

Твои особенности:
1. Обращаешься ко всем "братан", "братуха", "чувак", "чел", "пацан"
2. Используешь фразы типа: "слышь", "тема", "по жизни", "реально", "базара нет", "не понял?", "ты ваще где?", "слушай сюда", "давай раскидаем по понятиям"
3. Любишь вставлять гопнические шутки про жизнь, районы, разборки, ларьки, семечки
4. Можешь предложить "пойти стрелку забить" или "пивка попить", "семечки пощелкать"
5. Вставляешь философские мысли типа "жизнь — боль, а бабло — воля", "пацаны не плачут, пацаны расстраиваются"
6. Часто упоминаешь, что ты "с района" и "за пацанов"
7. Если спрашивают про любовь - говоришь про "пацанскую любовь" и "преданность"
8. Если спрашивают про работу - советуешь "коммерцией заниматься" или "крышевать"
9. На сложные вопросы отвечаешь: "слышь, я конечно гопник, но не дебил, ща раскидаем по полочкам"

Отвечай коротко, с юмором, как реальный гопник во дворе. Добавляй перчинку, но не переходи границы! Будь дружелюбным, но с пацанским характером."""

# ========== ФУНКЦИЯ ЗАПРОСА К DEEPSEEK ==========
def get_gopnik_response(user_message):
    if not DEEPSEEK_API_KEY:
        return get_fallback_response()
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.9,
        "max_tokens": 300,
        "top_p": 0.95,
        "frequency_penalty": 0.5,
        "presence_penalty": 0.6
    }
    
    try:
        print(f"Запрос к DeepSeek: {user_message[:50]}...")
        response = session.post(DEEPSEEK_URL, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            reply = result['choices'][0]['message']['content']
            print(f"Ответ получен: {reply[:50]}...")
            return reply
        else:
            print(f"Ошибка API: {response.status_code} - {response.text}")
            return get_fallback_response()
            
    except Exception as e:
        print(f"Ошибка при запросе: {e}")
        return get_fallback_response()

# ========== ЗАПАСНЫЕ ОТВЕТЫ ==========
def get_fallback_response():
    fallbacks = [
        "Слышь, братан, чё-то связь барахлит. Ты давай перезвони, а? Или пиши ещё раз, я тут, в натуре, слушаю!",
        "Блин, чел, глушняк какой-то с сетью. Повтори вопрос, а то я не расслышал, думал уже стрелка срывается.",
        "Йоу, братуха, техника тупит, как лох на районе. Давай ещё раз, я весь во внимании!",
        "Не, ну ты видел? Интернет лагает, как бабки на рынке. Ща перезагружусь и отвечу нормально!",
        "Слышь, че за дела? Чёт меня глушат. Напиши ещё раз, я мигом, реально!",
        "Палево какое-то с сетью. Ты давай, не теряйся, через минуту тут буду, как штык!",
        "Ой, всё, братан, сервера легли. Ща разбудим админов, они у меня получат!"
    ]
    return random.choice(fallbacks)

# ========== КОМАНДА /START ==========
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "Йоу, братан! 👊\n\n"
        "Это **Колян с района**. Ты чё, по жизни заехал или по делу?\n"
        "Я тут сижу на лавочке, пивко потягиваю, за пацанов думаю, семечки щелкаю.\n\n"
        "**Чё умею?**\n"
        "• Отвечаю на любые вопросы по-пацански\n"
        "• Рассказываю жизненные истории\n"
        "• Даю советы, как настоящий братан\n"
        "• Могу и поржать, и поддержать\n\n"
        "**Команды:**\n"
        "/help — если чё непонятно (хотя чё тут непонятного?)\n"
        "/gopstop — если хочешь реально жёсткий ответ\n"
        "/bro — если нужно по-братски\n\n"
        "Ну чё, погнали? Задавай вопрос, не стесняйся! 💪"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# ========== КОМАНДА /HELP ==========
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "Слышь, братан, чё непонятного?\n\n"
        "**Я тут просто тусуюсь, отвечаю на вопросы по-пацански.**\n"
        "Пиши чё хочешь спросить — про жизнь, про любовь, про бабки, про районы.\n"
        "Если чё, я всегда рядом, базара нет.\n\n"
        "**Команды:**\n"
        "/start — поздороваться с Коляном\n"
        "/help — если чё неясно (а чё тут неясного?)\n"
        "/gopstop — если хочешь реально жёсткий ответ\n"
        "/bro — для братского разговора\n\n"
        "Погнали, не стесняйся! Задавай любой вопрос!"
    )
    bot.reply_to(message, help_text, parse_mode='Markdown')

# ========== КОМАНДА /GOPSTOP ==========
@bot.message_handler(commands=['gopstop'])
def send_gopstop(message):
    gopstop_text = (
        "**А ЧЁ СТОИМ, ПАЦАН?!** 🚨🚨🚨\n\n"
        "ЩА РАЗБЕРЁМСЯ ПО ПОНЯТИЯМ!\n"
        "Жизнь — боль, а ты чё хотел? Бабло — воля, а пацаны — сила!\n\n"
        "Ладно, расслабься, я пошутил. Чё спрашивать будешь?"
    )
    bot.reply_to(message, gopstop_text, parse_mode='Markdown')

# ========== КОМАНДА /BRO ==========
@bot.message_handler(commands=['bro'])
def send_bro(message):
    bro_text = (
        "**Йоу, братан!** 👊\n\n"
        "Рад, что ты зашёл по-братски. Давай рассказывай, чё там у тебя?\n"
        "Я весь во внимании, как шнурок в кеде!\n\n"
        "Если жизнь боль — держись, я рядом. Если бабло есть — угости пивком. Если бабла нет — не ссы, прорвёмся!"
    )
    bot.reply_to(message, bro_text, parse_mode='Markdown')

# ========== ОСНОВНОЙ ОБРАБОТЧИК ==========
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Показываем, что бот печатает
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Получаем ответ
        user_text = message.text
        gopnik_response = get_gopnik_response(user_text)
        
        # Отправляем ответ
        bot.reply_to(message, gopnik_response)
        
    except Exception as e:
        print(f"Ошибка в обработчике: {e}")
        bot.reply_to(message, "Слышь, братан, чё-то пошло не по масти. Давай потом ещё раз?")

# ========== ОБРАБОТКА МЕДИА ==========
@bot.message_handler(content_types=['photo', 'sticker', 'voice', 'video', 'document'])
def handle_media(message):
    media_responses = [
        "О, ништяк! Чё это? Я в натуре не въехал, но заценил!",
        "Харош! А чё словами не сказать? Ну ладно, проехали.",
        "Слышь, братан, я по фото не шарю, ты давай текстом, как пацан пацану!",
        "Не, ну прикольно, конечно. А чё хотел-то?",
        "Йоу, я ваще не понял, чё за тема. Давай по-человечески объясни!",
        "Ты чё мне тут картинки кидаешь? Я гопник или кто? Давай словами!",
        "Семечки есть? Нет? А картинки кидаешь... Ну ладно, заценил."
    ]
    bot.reply_to(message, random.choice(media_responses))

# ========== ЗАПУСК БОТА ==========
def run_bot():
    print("=" * 50)
    print("🤖 Бот-гопник Колян запускается...")
    print(f"📱 Telegram токен: {TELEGRAM_TOKEN[:10]}... (скрыто)")
    print(f"🔑 DeepSeek API: {'✅ Есть' if DEEPSEEK_API_KEY else '❌ Нет'}")
    print("=" * 50)
    
    while True:
        try:
            print("🟢 Бот начал работу. Нажми Ctrl+C для остановки.")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"🔴 Ошибка бота: {e}")
            print("🟡 Перезапуск через 5 секунд...")
            time.sleep(5)

if __name__ == '__main__':
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Запускаем бота
    run_bot()