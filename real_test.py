import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

class RealChatTest:
    def __init__(self):
        self.chat_id = f"test_{int(time.time())}"
        
    def send_webhook(self, role, text, delay_seconds=0):
        """Отправляет имитацию вебхука от Wazzup"""
        if delay_seconds > 0:
            time.sleep(delay_seconds)
        
        is_operator = (role == "manager")
        
        webhook_data = {
            "type": "message",
            "message": {
                "id": f"msg_{int(time.time() * 1000)}",
                "chatId": self.chat_id,
                "text": text,
                "sender": {
                    "type": "operator" if is_operator else "contact",
                    "name": "Тест Менеджер" if is_operator else "Тест Клиент",
                    "id": "manager_001" if is_operator else self.chat_id
                },
                "timestamp": int(time.time())
            }
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/webhook/wazzup",
                json=webhook_data,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"✅ {role.upper()}: {text}")
                return True
            else:
                print(f"❌ Ошибка отправки: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение: {e}")
            return False
    
    def run_test_scenario(self, scenario_name="default"):
        """Запускает тестовый сценарий диалога"""
        
        print(f"\n🎬 СЦЕНАРИЙ: {scenario_name.upper()}")
        print("=" * 60)
        
        if scenario_name == "bad_manager":
            # ПЛОХОЙ менеджер (для демонстрации ошибок)
            messages = [
                ("client", "Добрый день! У меня проблема с доставкой"),
                ("manager", "Что?", 2),
                ("client", "Заказ не приходит 2 недели", 5),
                ("manager", "Номер", 3),
                ("client", "ORD-789456", 4),
                ("manager", "Ждите", 10),
                ("client", "А когда примерно?", 5),
                ("manager", "Не знаю", 15)
            ]
            
        elif scenario_name == "good_manager":
            # ХОРОШИЙ менеджер
            messages = [
                ("client", "Здравствуйте! Не могу отследить свой заказ #12345"),
                ("manager", "Добрый день, Иван! Спасибо за обращение. Сейчас проверю информацию по вашему заказу.", 3),
                ("manager", "Вижу ваш заказ. Он был отправлен 20 января. Вот трек-номер для отслеживания: RA123456789RU", 5),
                ("client", "Спасибо! А примерные сроки доставки?", 4),
                ("manager", "Обычно доставка занимает 7-10 рабочих дней. Рекомендую отслеживать на сайте почты России. Нужна еще помощь?", 6),
                ("client", "Нет, спасибо, все понятно!", 3),
                ("manager", "Отлично! Приятного дня! Если будут вопросы - обращайтесь 👍", 2)
            ]
            
        else:
            # СМЕШАННЫЙ сценарий (обычный)
            messages = [
                ("client", "Привет, заказ не пришел"),
                ("manager", "Здравствуйте. Какой номер заказа?", 3),
                ("client", "ORD-123", 5),
                ("manager", "Проверил. Отправили вчера", 8),
                ("client", "А трек номер есть?", 4),
                ("manager", "Да, RB987654321CN", 6),
                ("client", "Спасибо", 3)
            ]
        
        # Отправляем все сообщения
        for msg in messages:
            if len(msg) == 2:
                role, text = msg
                delay = 0
            else:
                role, text, delay = msg
            
            self.send_webhook(role, text, delay)
        
        print("\n💾 Диалог сохранен!")
        print(f"📱 ID чата: {self.chat_id}")
    
    def analyze_chat(self):
        """Запускает анализ чата"""
        print(f"\n🤖 ЗАПУСКАЮ АНАЛИЗ ЧАТА {self.chat_id}")
        print("-" * 40)
        
        try:
            # Запускаем анализ
            response = requests.post(
                f"{BASE_URL}/analyze/{self.chat_id}",
                params={"force": True, "background": False},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Красиво выводим результат
                self.print_analysis_result(result)
                
                # Сохраняем в файл
                with open(f"logs/analysis_{self.chat_id}.json", "w") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                print(f"\n💾 Результат сохранен в: logs/analysis_{self.chat_id}.json")
                
                return result
            else:
                print(f"❌ Ошибка анализа: {response.status_code}")
                print(response.text)
                return None
                
        except Exception as e:
            print(f"❌ Исключение при анализе: {e}")
            return None
    
    def print_analysis_result(self, result):
        """Красивый вывод результата анализа"""
        print(f"\n📊 РЕЗУЛЬТАТ АНАЛИЗА")
        print("=" * 50)
        
        if result.get("error"):
            print(f"❌ Ошибка: {result.get('error_message')}")
            return
        
        # Основная информация
        print(f"📋 ВЫЖИМКА: {result.get('summary', 'Нет данных')}")
        print(f"🎯 ОБЩАЯ ОЦЕНКА: {result.get('total_score', 0)}/50")
        print(f"⭐ РЕЙТИНГ: {result.get('rating', '')}")
        
        # Оценки по критериям
        if "scores" in result:
            print("\n📈 ОЦЕНКА ПО КРИТЕРИЯМ:")
            scores = result["scores"]
            for criterion, score in scores.items():
                bar = "█" * int(score / 2) + "░" * (5 - int(score / 2))
                criterion_name = {
                    "politeness": "Вежливость",
                    "professionalism": "Профессионализм",
                    "proactivity": "Проактивность",
                    "response_speed": "Скорость реакции",
                    "whatsapp_effectiveness": "WhatsApp-эффективность"
                }.get(criterion, criterion)
                
                print(f"  {criterion_name:25} {score:2}/10 {bar}")
        
        # Ошибки
        if result.get("key_errors"):
            print("\n❌ ОСНОВНЫЕ ОШИБКИ:")
            for error in result["key_errors"][:3]:
                print(f"  • {error}")
        
        # Советы
        if result.get("improvement_suggestions"):
            print("\n💡 СОВЕТЫ ПО УЛУЧШЕНИЮ:")
            for suggestion in result["improvement_suggestions"][:3]:
                print(f"  • {suggestion}")
        
        # WhatsApp особенности
        if result.get("whatsapp_specific_notes"):
            print("\n📱 WHATSAPP-ОСОБЕННОСТИ:")
            for note in result["whatsapp_specific_notes"][:2]:
                print(f"  • {note}")
        
        print("=" * 50)
    
    def check_chat_in_db(self):
        """Проверяет сохранение чата в базе"""
        try:
            response = requests.get(f"{BASE_URL}/chats/{self.chat_id}", timeout=5)
            
            if response.status_code == 200:
                chat_data = response.json()
                messages = chat_data.get("chat", {}).get("messages", [])
                
                print(f"\n📁 ЧАТ В БАЗЕ:")
                print(f"  ID: {self.chat_id}")
                print(f"  Сообщений: {len(messages)}")
                print(f"  Источник: {chat_data.get('chat', {}).get('source', 'unknown')}")
                
                # Показываем последние сообщения
                print("\n💬 ПОСЛЕДНИЕ СООБЩЕНИЯ:")
                for msg in messages[-3:]:
                    role_emoji = "👤" if msg["role"] == "client" else "👨‍💼"
                    print(f"  {role_emoji} {msg['role'].upper()}: {msg['text'][:50]}...")
                
                return True
            else:
                print(f"❌ Чат не найден: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка проверки чата: {e}")
            return False

def run_complete_test():
    """Запускает полный тест"""
    print("🧪 ПОЛНЫЙ ТЕСТ СИСТЕМЫ С РЕАЛЬНЫМ ЧАТОМ")
    print("=" * 60)
    
    # Создаем тестер
    tester = RealChatTest()
    
    # Выбираем сценарий
    print("\n🎭 ВЫБЕРИ СЦЕНАРИЙ ТЕСТА:")
    print("1. Плохой менеджер (покажет много ошибок)")
    print("2. Хороший менеджер (высокая оценка)")
    print("3. Обычный диалог (смешанный)")
    
    choice = input("\nВведи номер (1-3): ").strip()
    
    scenarios = {
        "1": "bad_manager",
        "2": "good_manager",
        "3": "default"
    }
    
    scenario = scenarios.get(choice, "default")
    
    # Запускаем сценарий
    tester.run_test_scenario(scenario)
    
    # Проверяем сохранение
    print("\n" + "=" * 40)
    tester.check_chat_in_db()
    
    # Запускаем анализ
    print("\n" + "=" * 40)
    analysis_result = tester.analyze_chat()
    
    # Показываем API для дальнейшей работы
    print("\n" + "=" * 60)
    print("🚀 API ДЛЯ РАБОТЫ С ЭТИМ ЧАТОМ:")
    print(f"GET  /chats/{tester.chat_id} - просмотр чата")
    print(f"POST /analyze/{tester.chat_id} - повторный анализ")
    print(f"GET  /analysis/{tester.chat_id} - результат анализа")
    print(f"GET  /dashboard - общая статистика")
    
    return analysis_result is not None

if __name__ == "__main__":
    # Проверяем что сервер запущен
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=3)
        if response.status_code == 200:
            print("✅ Сервер работает")
            run_complete_test()
        else:
            print("❌ Сервер не отвечает. Запусти: python main.py")
    except:
        print("❌ Сервер не запущен. Запусти в другом окне:")
        print("   uvicorn main:app --reload")