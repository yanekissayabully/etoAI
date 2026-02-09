import requests
import json
import time
from datetime import datetime

def test_local_server():
    """Тестируем локальный сервер"""
    print("🔄 Тестируем локальный сервер...")
    
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"✅ Сервер жив: {response.json()}")
    except:
        print("❌ Сервер не запущен. Запусти: python main.py")
        return False
    
    return True

def test_openai():
    """Тестируем подключение к OpenAI"""
    print("\n🧠 Тестируем OpenAI...")
    
    try:
        import openai
        from dotenv import load_dotenv
        load_dotenv()
        
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        # Быстрый тестовый запрос
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Скажи привет"}],
            max_tokens=10
        )
        
        print(f"✅ OpenAI работает: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI ошибка: {e}")
        return False

def test_analyzer():
    """Тестируем анализатор на тестовом диалоге"""
    print("\n🔍 Тестируем анализатор...")
    
    test_chat = [
        {"role": "client", "text": "Добрый день! У меня проблема с заказом #12345"},
        {"role": "manager", "text": "Здравствуйте. Что случилось?"},
        {"role": "client", "text": "Не приходит трек номер, уже 3 дня"},
        {"role": "manager", "text": "Секунду, проверю..."},
        {"role": "manager", "text": "Отправили вчера. Вот трек: RA123456789RU"},
        {"role": "client", "text": "Спасибо! А когда примерно придет?"},
        {"role": "manager", "text": "Через 5-7 дней"},
        {"role": "client", "text": "Понял, спасибо!"}
    ]
    
    from analyzer import analyze_chat, print_analysis_pretty
    
    try:
        result = analyze_chat(test_chat)
        print_analysis_pretty(result)
        return True
    except Exception as e:
        print(f"❌ Ошибка анализатора: {e}")
        return False

def create_test_webhook():
    """Создаем тестовый вебхук для имитации WABA"""
    print("\n📨 Создаем тестовый вебхук...")
    
    test_payload = {
        "event": "message",
        "id": "test_123",
        "from": "79123456789",  # номер клиента
        "to": "79876543210",    # номер менеджера
        "body": "Привет! Тестирую ваш сервис",
        "timestamp": int(time.time()),
        "type": "chat"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/webhook",
            json=test_payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"✅ Тестовый вебхук отправлен: {response.json()}")
        
        # Проверяем сохранение
        response = requests.get("http://localhost:8000/chats")
        chats = response.json()
        print(f"📊 Сохранено диалогов: {len(chats.get('chats', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка вебхука: {e}")
        return False

if __name__ == "__main__":
    print("🧪 ЗАПУСК ТЕСТОВОГО СЦЕНАРИЯ")
    print("=" * 50)
    
    # Запускаем все тесты
    tests = [
        ("Локальный сервер", test_local_server),
        ("OpenAI", test_openai),
        ("Анализатор", test_analyzer),
        ("Вебхук", create_test_webhook)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Исключение в тесте {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n" + "="*50)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ:")
    
    all_passed = True
    for test_name, success in results:
        status = "✅ ПРОЙДЕН" if success else "❌ ПРОВАЛЕН"
        print(f"  {test_name}: {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Система готова к работе.")
        print("\n👉 Далее:")
        print("1. Настрой вебхук в Ultramsg на URL: http://ваш_адрес/webhook")
        print("2. Отправь сообщение в WABA")
        print("3. Проверь сохранение в GET /chats")
        print("4. Проанализируй через POST /analyze/{chat_id}")
    else:
        print("\n⚠️ Некоторые тесты не пройдены. Проверь конфигурацию.")