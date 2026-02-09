import requests
import json
import os
import sys
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def print_header(text):
    """Печатает заголовок"""
    print("\n" + "="*60)
    print(f"🧪 {text}")
    print("="*60)

def test_wazzup_connection():
    """Тестируем подключение к Wazzup"""
    print_header("ТЕСТ ПОДКЛЮЧЕНИЯ WAZZUP")
    
    api_key = os.getenv("WAZZUP_API_KEY")
    if not api_key:
        print("❌ WAZZUP_API_KEY не найден в .env файле")
        print("\n👉 Добавь в .env:")
        print('WAZZUP_API_KEY="твой_api_ключ_от_wazzup"')
        return False
    
    print(f"🔑 API Key: {api_key[:10]}...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        # Получаем список каналов
        response = requests.get(
            "https://api.wazzup.io/api/channels",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            channels = response.json()
            print(f"✅ Подключение успешно! Найдено каналов: {len(channels)}")
            
            # Показываем каналы
            whatsapp_channels = []
            for channel in channels:
                channel_type = channel.get("type", "unknown")
                channel_name = channel.get("name", "Без названия")
                channel_id = channel.get("id")
                active = channel.get("active", False)
                
                status = "✅ Активен" if active else "❌ Не активен"
                
                print(f"   📱 {channel_name} ({channel_type}) - {status}")
                
                if channel_type == "whatsapp" and active:
                    whatsapp_channels.append(channel)
            
            # WhatsApp каналы
            if whatsapp_channels:
                print(f"\n📱 Найдено WhatsApp каналов: {len(whatsapp_channels)}")
                for wc in whatsapp_channels:
                    print(f"   • {wc.get('name')} (ID: {wc.get('id')})")
                    
                    # Проверяем ID в .env
                    env_channel_id = os.getenv("WAZZUP_CHANNEL_ID")
                    if not env_channel_id:
                        print(f"\n⚠️  WAZZUP_CHANNEL_ID не указан в .env")
                        print(f"👉 Добавь в .env:")
                        print(f'WAZZUP_CHANNEL_ID="{wc.get("id")}"')
                    elif env_channel_id != wc.get("id"):
                        print(f"⚠️  ID в .env ({env_channel_id}) не совпадает с активным каналом")
            else:
                print("\n❌ Нет активных WhatsApp каналов!")
                print("👉 Зайди в личный кабинет Wazzup и настрой WhatsApp канал")
                return False
            
            return True
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"Ответ сервера: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Не удалось подключиться к Wazzup API")
        print("👉 Проверь интернет-подключение")
        return False
    except requests.exceptions.Timeout:
        print("❌ Таймаут подключения к Wazzup")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_local_server():
    """Тестируем локальный сервер"""
    print_header("ТЕСТ ЛОКАЛЬНОГО СЕРВЕРА")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Сервер работает! Статус: {data.get('status')}")
            
            # Проверяем компоненты
            components = data.get("components", {})
            print("\n🔧 Компоненты:")
            for comp, status in components.items():
                status_icon = "✅" if status in ["healthy", "configured", "enabled"] else "⚠️"
                print(f"   {status_icon} {comp}: {status}")
            
            return True
        else:
            print(f"❌ Сервер ответил с ошибкой: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Сервер не запущен")
        print("👉 Запусти сервер: python main.py")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def setup_webhook():
    """Настраиваем вебхук в Wazzup"""
    print_header("НАСТРОЙКА ВЕБХУКА")
    
    # Получаем URL от пользователя
    print("\nДля получения сообщений от Wazzup нужен публичный URL.")
    print("1. Запусти ngrok в отдельном окне: ngrok http 8000")
    print("2. Скопируй https URL (например: https://abc123.ngrok.io)")
    
    webhook_url = input("\nВведи твой публичный URL (или нажми Enter для пропуска): ").strip()
    
    if not webhook_url:
        print("⚠️  Пропускаем настройку вебхука")
        return False
    
    # Добавляем endpoint
    if not webhook_url.endswith("/webhook/wazzup"):
        webhook_url = webhook_url.rstrip("/") + "/webhook/wazzup"
    
    print(f"\n🔗 Настраиваю вебхук: {webhook_url}")
    
    api_key = os.getenv("WAZZUP_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": webhook_url,
        "events": ["message", "message.status", "chat.closed"],
        "active": True
    }
    
    try:
        response = requests.post(
            "https://api.wazzup.io/api/webhook",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ Вебхук успешно настроен!")
            print(f"   ID вебхука: {result.get('id')}")
            print(f"   URL: {result.get('url')}")
            print(f"   События: {', '.join(result.get('events', []))}")
            return True
        else:
            print(f"❌ Ошибка настройки вебхука: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def send_test_message():
    """Отправляем тестовое сообщение через Wazzup"""
    print_header("ОТПРАВКА ТЕСТОВОГО СООБЩЕНИЯ")
    
    api_key = os.getenv("WAZZUP_API_KEY")
    channel_id = os.getenv("WAZZUP_CHANNEL_ID")
    
    if not channel_id:
        print("❌ WAZZUP_CHANNEL_ID не найден в .env")
        return False
    
    # Номер для теста
    print("\nДля теста нужен номер WhatsApp в формате 79123456789")
    print("Используй номер, на который настроен Wazzup канал")
    
    phone = input("Введи номер телефона (или нажми Enter для пропуска): ").strip()
    
    if not phone:
        print("⚠️  Пропускаем отправку сообщения")
        return False
    
    # Проверяем формат номера
    if not phone.startswith("7") or len(phone) != 11:
        print(f"⚠️  Номер {phone} может быть в неверном формате")
        print("👉 Используй формат: 79123456789")
        confirm = input("Все равно отправить? (y/n): ").strip().lower()
        if confirm != 'y':
            return False
    
    message = "🤖 Привет! Это тестовое сообщение от AI-анализатора чатов. Ответь что-нибудь для теста анализа системы."
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "channelId": channel_id,
        "chatId": phone,
        "text": message,
        "type": "text"
    }
    
    print(f"\n📤 Отправляю сообщение на {phone}...")
    print(f"💬 Текст: {message[:50]}...")
    
    try:
        response = requests.post(
            "https://api.wazzup.io/api/message",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Сообщение отправлено успешно!")
            print(f"   ID сообщения: {result.get('id')}")
            print(f"   Статус: {result.get('status', 'unknown')}")
            
            # Проверяем сохранение в нашем сервере
            print("\n🔄 Проверяю сохранение в нашей системе...")
            try:
                check_response = requests.get(
                    f"http://localhost:8000/chats/{phone}",
                    timeout=5
                )
                
                if check_response.status_code == 200:
                    print("✅ Сообщение сохранено в нашей базе!")
                else:
                    print(f"⚠️  Сообщение не найдено в нашей базе (код: {check_response.status_code})")
            except:
                print("⚠️  Не удалось проверить сохранение")
            
            return True
        else:
            print(f"❌ Ошибка отправки: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_ai_analyzer():
    """Тестируем ИИ-анализатор"""
    print_header("ТЕСТ ИИ-АНАЛИЗАТОРА")
    
    # Проверяем OpenAI ключ
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY не найден в .env")
        print("\n👉 Добавь в .env:")
        print('OPENAI_API_KEY="sk-твой_ключ_openai"')
        return False
    
    print(f"🔑 OpenAI Key: {openai_key[:10]}...")
    
    # Тестовый диалог
    test_chat = [
        {"role": "client", "text": "Здравствуйте, не могу отследить заказ #78910"},
        {"role": "manager", "text": "Добрый день! Сейчас проверю информацию по вашему заказу."},
        {"role": "manager", "text": "Ваш заказ отправлен 20 января. Трек-номер: RB123456789RU"},
        {"role": "client", "text": "Спасибо! А когда примерно ждать доставку?"},
        {"role": "manager", "text": "Обычно 7-10 рабочих дней. Отслеживайте по треку на сайте почты."},
        {"role": "client", "text": "Понял, спасибо за помощь!"}
    ]
    
    print("\n🤖 Анализирую тестовый диалог...")
    
    try:
        # Импортируем анализатор
        from analyzer import analyze_chat, print_analysis_pretty
        
        result = analyze_chat(test_chat)
        
        if result.get("error"):
            print(f"❌ Ошибка анализа: {result.get('error_message')}")
            return False
        
        print_analysis_pretty(result)
        
        # Сохраняем результат
        with open("logs/test_analysis_result.json", "w") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print("✅ Анализ завершен! Результат сохранен в logs/test_analysis_result.json")
        return True
        
    except ImportError:
        print("❌ Не удалось импортировать analyzer.py")
        return False
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")
        return False

def main_menu():
    """Главное меню тестов"""
    while True:
        print_header("ГЛАВНОЕ МЕНЮ ТЕСТОВ")
        print("1. 🔗 Тест подключения к Wazzup")
        print("2. 🖥️  Тест локального сервера")
        print("3. 🪝 Настройка вебхука Wazzup")
        print("4. 📤 Отправить тестовое сообщение")
        print("5. 🤖 Тест ИИ-анализатора")
        print("6. 🧪 Запустить все тесты")
        print("7. 🚀 Инструкция по запуску")
        print("8. 🚪 Выход")
        
        choice = input("\nВыбери опцию (1-8): ").strip()
        
        if choice == "1":
            test_wazzup_connection()
        elif choice == "2":
            test_local_server()
        elif choice == "3":
            setup_webhook()
        elif choice == "4":
            send_test_message()
        elif choice == "5":
            test_ai_analyzer()
        elif choice == "6":
            run_all_tests()
        elif choice == "7":
            show_instructions()
        elif choice == "8":
            print("\n👋 Выход...")
            break
        else:
            print("❌ Неверный выбор. Попробуй снова.")
        
        input("\nНажми Enter чтобы продолжить...")

def run_all_tests():
    """Запускает все тесты последовательно"""
    print_header("ЗАПУСК ВСЕХ ТЕСТОВ")
    
    tests = [
        ("Подключение к Wazzup", test_wazzup_connection),
        ("Локальный сервер", test_local_server),
        ("ИИ-анализатор", test_ai_analyzer),
        # ("Настройка вебхука", setup_webhook),
        # ("Отправка сообщения", send_test_message)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Тест: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
            print(f"   {'✅ Успех' if success else '❌ Провал'}")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            results.append((test_name, False))
    
    print_header("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    
    all_passed = True
    for test_name, success in results:
        status = "✅ ПРОЙДЕН" if success else "❌ ПРОВАЛЕН"
        print(f"  {test_name:30} {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Система готова к работе.")
        print("\n👉 Следующие шаги:")
        print("1. Настрой вебхук (опция 3 в меню)")
        print("2. Отправь тестовое сообщение (опция 4)")
        print("3. Проверь сохранение в браузере: http://localhost:8000/chats")
        print("4. Проанализируй чат: http://localhost:8000/analyze/{номер}")
    else:
        print("\n⚠️ Некоторые тесты не пройдены. Проверь конфигурацию.")

def show_instructions():
    """Показывает инструкцию по запуску"""
    print_header("ПОЛНАЯ ИНСТРУКЦИЯ ПО ЗАПУСКУ")
    
    print("""
1. 📦 УСТАНОВКА ЗАВИСИМОСТЕЙ:
   ```bash
   pip install -r requirements.txt""")