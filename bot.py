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
print("💀 УБИВАЕМ ВСЕ СТАРЫЕ ПОДКЛЮЧЕНИЯ...")
urls = [
    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook",
    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/close",
    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url=",
]
for url in urls:
    try:
        r = requests.get(url)
        print(f"{url}: {r.status_code}")
    except:
        pass
time.sleep(3)

# ========== ПРОВЕРКА GUNICORN ==========
if 'gunicorn' in sys.argv[0] or 'GUNICORN_CMD_ARGS' in os.environ:
    app = Flask(__name__)
    @app.route('/')
    def index(): return "Колян жив"
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
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

def add_to_history(chat_id, role, text):
    if chat_id not in chat_history:
        chat_history[chat_id] = deque(maxlen=10)
    chat_history[chat_id].append((role, text))

# ========== БОТ ==========
bot = None
is_worker = os.environ.get('WORKER') == 'true'

if is_worker:
    try:
        bot = telebot.TeleBot(TELEGRAM_TOKEN)
        me = bot.get_me()
        print(f"✅ БОТ ЗАПУЩЕН: @{me.username}")
        print(f"✅ ID: {me.id}")
        print(f"✅ Имя: {me.first_name}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

SYSTEM_PROMPT = """Ты — гопник Колян. Отвечаешь дерзко, с матом, но по делу.

ПРАВИЛА:
1. Матерись, но не переходи границы
2. Отвечай ПОЛНОСТЬЮ, не обрывай на полуслове
3. Если просят код — пиши код
4. Используй слова: бля, сука, нахер, братан"""

# ========== ФУНКЦИЯ ОТВЕТА ==========
def get_gopnik_response(user_message, chat_id):
    try:
        add_to_history(chat_id, "user", user_message)
        
        # Собираем историю
        history_text = ""
        if chat_id in chat_history:
            for role, text in list(chat_history[chat_id])[-5:]:  # последние 5 сообщений
                history_text += f"{'Колян' if role=='assistant' else 'Чел'}: {text}\n"
        
        prompt = f"""{SYSTEM_PROMPT}

История разговора:
{history_text}

Чел: {user_message}
Колян (ответь полностью, не обрывай, с матом, но по делу):"""
        
        # Пробуем разные модели
        models = [
            "gemini-1.5-flash",
            "gemini-pro",
        ]
        
        for model_name in models:
            try:
                print(f"🔄 Пробую {model_name}...")
                
                # ВАЖНО: timeout НЕ передаём в модель
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config=generation_config
                )
                
                # timeout передаём ТОЛЬКО сюда
                resp = model.generate_content(
                    prompt,
                    request_options={"timeout": 15}  # ✅ правильный способ
                )
                
                if resp and hasattr(resp, 'text') and resp.text:
                    reply = resp.text.strip()
                    print(f"✅ Ответ от {model_name}")
                    add_to_history(chat_id, "assistant", reply)
                    return reply
                else:
                    print(f"⚠️ Пустой ответ от {model_name}")
                    
            except Exception as e:
                print(f"❌ {model_name} ошибка: {e}")
                continue
        
        return "Техника тупит, бля. Повтори вопрос, братан."
        
    except Exception as e:
        print(f"💥 Ошибка: {e}")
        return "Ошибка, сорян. Давай ещё раз."

# ========== КОМАНДЫ ==========
if bot:
    @bot.message_handler(commands=['start'])
    def start(message):
        chat_id = message.chat.id
        if chat_id in chat_history:
            del chat_history[chat_id]
        bot.send_message(
            chat_id,
            "Йоу, бля! 👊\n\n"
            "Я **Колян**, на связи!\n"
            "Спрашивай что хочешь — отвечу по-пацански."
        )

    @bot.message_handler(func=lambda message: True)
    def handle_message(message):
        try:
            bot.send_chat_action(message.chat.id, 'typing')
            reply = get_gopnik_response(message.text, message.chat.id)
            bot.send_message(message.chat.id, reply)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            bot.send_message(message.chat.id, "Ошибка, братан. Попробуй ещё.")

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    print("=" * 50)
    print(f"🚀 Режим: {'WORKER' if is_worker else 'WEB'}")
    
    if is_worker and bot:
        print("🤬 Колян запущен и готов!")
        try:
            bot.infinity_polling()
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            time.sleep(5)
    else:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
