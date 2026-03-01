# ========== ФУНКЦИЯ ЗАПРОСА ==========
def get_gopnik_response(user_message):
    # Пробуем Wisdom Gate (бесплатно, без ключа)
    try:
        WISDOM_URL = "https://wisdom-gate.juheapi.com/v1/chat/completions"
        
        data = {
            "model": "deepseek-r1",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            "temperature": 1.1,
            "max_tokens": 500
        }
        
        print(f"🤔 Запрос к Wisdom Gate...")
        response = requests.post(WISDOM_URL, json=data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            reply = result['choices'][0]['message']['content']
            print(f"✅ Ответ от Wisdom получен")
            return reply
        else:
            print(f"❌ Wisdom ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Wisdom исключение: {e}")
    
    # Пробуем OpenRouter как запасной
    try:
        OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
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
            "temperature": 1.1
        }
        
        print(f"🤔 Запрос к OpenRouter...")
        response = requests.post(OPENROUTER_URL, headers=headers, json=data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            reply = result['choices'][0]['message']['content']
            print(f"✅ Ответ от OpenRouter получен")
            return reply
    except Exception as e:
        print(f"❌ OpenRouter исключение: {e}")
    
    # Если всё упало - возвращаем запасной ответ
    print("⚠️ Все API упали, используем fallback")
    return get_fallback_response()
