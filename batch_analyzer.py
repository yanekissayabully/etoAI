import requests
import json
import sys
import csv
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def batch_analyze_from_cli():
    """Утилита для массового анализа из командной строки"""
    
    print("🔍 МАССОВЫЙ АНАЛИЗ ДИАЛОГОВ")
    print("=" * 50)
    
    # Получаем список чатов
    print("📂 Получаю список диалогов...")
    response = requests.get(f"{BASE_URL}/chats?limit=100")
    
    if response.status_code != 200:
        print(f"❌ Ошибка: {response.text}")
        return
    
    chats = response.json().get("chats", [])
    
    if not chats:
        print("❌ Нет диалогов для анализа")
        return
    
    print(f"✅ Найдено {len(chats)} диалогов")
    
    # Фильтруем
    print("\n🎯 ФИЛЬТРАЦИЯ ДИАЛОГОВ")
    print("1. Все диалоги")
    print("2. Только за последние 7 дней")
    print("3. Только с определенным менеджером")
    print("4. Только не анализированные")
    print("5. Только с минимумом сообщений")
    
    choice = input("\nВыбери опцию (1-5): ").strip()
    
    filtered_chats = []
    
    if choice == "1":
        filtered_chats = chats
    elif choice == "2":
        week_ago = datetime.now() - timedelta(days=7)
        for chat in chats:
            try:
                chat_date = datetime.fromisoformat(chat["last_updated"].replace('Z', '+00:00'))
                if chat_date > week_ago:
                    filtered_chats.append(chat)
            except:
                filtered_chats.append(chat)
    elif choice == "3":
        manager_id = input("Введи ID менеджера: ").strip()
        filtered_chats = [c for c in chats if c.get("manager_id") == manager_id]
    elif choice == "4":
        # Нужно получить список уже проанализированных
        response = requests.get(f"{BASE_URL}/dashboard")
        if response.status_code == 200:
            dashboard = response.json()
            analyzed_ids = [a["chat_id"] for a in dashboard.get("recent_analyses", [])]
            filtered_chats = [c for c in chats if c["id"] not in analyzed_ids]
        else:
            filtered_chats = chats
    elif choice == "5":
        min_msgs = input("Минимум сообщений (например, 5): ").strip()
        try:
            min_msgs = int(min_msgs)
            filtered_chats = [c for c in chats if c.get("message_count", 0) >= min_msgs]
        except:
            print("❌ Неверное число, использую минимум 3 сообщения")
            filtered_chats = [c for c in chats if c.get("message_count", 0) >= 3]
    
    if not filtered_chats:
        print("❌ Нет диалогов по выбранным критериям")
        return
    
    print(f"\n📊 Будет проанализировано: {len(filtered_chats)} диалогов")
    
    # Выбираем сколько анализировать
    limit = input(f"Сколько диалогов анализировать? (макс {len(filtered_chats)}): ").strip()
    try:
        limit = int(limit)
        if limit > len(filtered_chats):
            limit = len(filtered_chats)
    except:
        limit = len(filtered_chats)
    
    # Способ анализа
    print("\n⚡ СПОСОБ АНАЛИЗА")
    print("1. Синхронно (последовательно, видно прогресс)")
    print("2. Асинхронно (пакетно, быстрее)")
    
    method_choice = input("Выбери способ (1-2): ").strip()
    
    if method_choice == "2":
        # Асинхронный массовый анализ через API
        print(f"\n🚀 Запускаю массовый анализ {limit} диалогов...")
        
        chat_ids = [c["id"] for c in filtered_chats[:limit]]
        
        # Используем API для массового анализа
        response = requests.post(
            f"{BASE_URL}/analyze/batch",
            params={
                "limit": limit,
                "background": True
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            task_ids = result.get("task_ids", [])
            print(f"✅ Запущено {len(task_ids)} задач анализа")
            print(f"🔧 ID задач: {', '.join(task_ids)}")
            
            # Ждем завершения (опционально)
            wait = input("\nЖдать завершения анализа? (y/n): ").strip().lower()
            if wait == 'y':
                print("⏳ Жду завершения... (проверяю каждые 5 секунд)")
                for task_id in task_ids:
                    while True:
                        status_resp = requests.get(f"{BASE_URL}/analyze/batch/status/{task_id}")
                        if status_resp.status_code == 200:
                            status = status_resp.json()
                            if status.get("status") == "completed":
                                print(f"✅ Задача {task_id} завершена")
                                break
                        time.sleep(5)
        else:
            print(f"❌ Ошибка массового анализа: {response.text}")
    
    else:
        # Синхронный анализ по одному
        print(f"\n🚀 Запускаю анализ {limit} диалогов...")
        
        chat_ids = [c["id"] for c in filtered_chats[:limit]]
        
        results = []
        for i, chat_id in enumerate(chat_ids, 1):
            print(f"\n[{i}/{len(chat_ids)}] Анализ диалога {chat_id}...")
            
            try:
                response = requests.post(
                    f"{BASE_URL}/analyze/{chat_id}",
                    params={"force": True, "background": False},
                    timeout=120
                )
                
                if response.status_code == 200:
                    result = response.json()
                    score = result.get("total_score", 0)
                    summary = result.get("summary", "")[:50]
                    
                    print(f"✅ Оценка: {score}/50 - {summary}")
                    
                    results.append({
                        "chat_id": chat_id,
                        "score": score,
                        "summary": summary,
                        "success": True
                    })
                else:
                    print(f"❌ Ошибка: {response.text}")
                    results.append({
                        "chat_id": chat_id,
                        "success": False,
                        "error": response.text[:100]
                    })
            
            except Exception as e:
                print(f"❌ Исключение: {e}")
                results.append({
                    "chat_id": chat_id,
                    "success": False,
                    "error": str(e)[:100]
                })
        
        # Итоги
        print("\n" + "="*50)
        print("📈 ИТОГИ МАССОВОГО АНАЛИЗА")
        print("="*50)
        
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        print(f"✅ Успешно: {len(successful)}")
        print(f"❌ Ошибки: {len(failed)}")
        
        if successful:
            scores = [r["score"] for r in successful]
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
            
            print(f"\n📊 СТАТИСТИКА ОЦЕНОК:")
            print(f"   Средняя оценка: {avg_score:.1f}/50")
            print(f"   Максимальная: {max_score}/50")
            print(f"   Минимальная: {min_score}/50")
            
            # Распределение по оценкам
            excellent = len([s for s in scores if s >= 45])
            good = len([s for s in scores if 35 <= s < 45])
            satisfactory = len([s for s in scores if 25 <= s < 35])
            poor = len([s for s in scores if s < 25])
            
            print(f"\n🏆 КАТЕГОРИИ:")
            print(f"   Отлично (45-50): {excellent}")
            print(f"   Хорошо (35-44): {good}")
            print(f"   Удовлетворительно (25-34): {satisfactory}")
            print(f"   Требует улучшения (0-24): {poor}")
        
        # Сохраняем результаты
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_json = f"logs/batch_analysis_{timestamp}.json"
        filename_csv = f"logs/batch_analysis_{timestamp}.csv"
        
        # JSON
        with open(filename_json, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total": len(results),
                "successful": len(successful),
                "failed": len(failed),
                "results": results
            }, f, ensure_ascii=False, indent=2)
        
        # CSV
        if successful:
            with open(filename_csv, "w", newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(["chat_id", "score", "category", "summary"])
                for r in successful:
                    score = r["score"]
                    if score >= 45:
                        category = "Отлично"
                    elif score >= 35:
                        category = "Хорошо"
                    elif score >= 25:
                        category = "Удовлетворительно"
                    else:
                        category = "Требует улучшения"
                    
                    writer.writerow([r['chat_id'], score, category, r.get('summary', '')[:100]])
            
            print(f"\n💾 Результаты сохранены:")
            print(f"   JSON: {filename_json}")
            print(f"   CSV: {filename_csv}")
        
        return results

def import_wazzup_history():
    """Импорт истории из Wazzup"""
    print("📥 ИМПОРТ ИСТОРИИ ИЗ WAZZUP")
    print("=" * 50)
    
    days = input("За сколько дней импортировать? (по умолчанию 7): ").strip()
    days_back = int(days) if days.isdigit() else 7
    
    limit = input("Сколько диалогов импортировать? (по умолчанию 20): ").strip()
    limit = int(limit) if limit.isdigit() else 20
    
    auto_analyze = input("Автоматически анализировать после импорта? (y/n): ").strip().lower()
    auto_analyze = auto_analyze == 'y'
    
    print(f"\n🚀 Импортирую {limit} диалогов за последние {days_back} дней...")
    
    response = requests.post(
        f"{BASE_URL}/import/wazzup/history",
        params={
            "days_back": days_back,
            "limit": limit,
            "auto_analyze": auto_analyze
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        imported = result.get("imported", 0)
        chat_ids = result.get("chat_ids", [])
        
        print(f"✅ Импортировано {imported} диалогов")
        
        if auto_analyze and imported > 0:
            print("🤖 Авто-анализ запущен...")
            # Можно сразу запустить анализ всех импортированных
            analyze_response = requests.post(
                f"{BASE_URL}/analyze/batch",
                params={
                    "limit": imported,
                    "background": True
                }
            )
            
            if analyze_response.status_code == 200:
                print("✅ Массовый анализ импортированных диалогов запущен")
        return True
    else:
        print(f"❌ Ошибка импорта: {response.text}")
        return False

def main_menu():
    """Главное меню утилиты"""
    while True:
        print("\n" + "="*60)
        print("🛠️  УТИЛИТА МАССОВОГО АНАЛИЗА WABA AI")
        print("="*60)
        print("1. 🔍 Массовый анализ сохраненных диалогов")
        print("2. 📥 Импорт истории из Wazzup")
        print("3. 📊 Показать статистику")
        print("4. 🚪 Выход")
        
        choice = input("\nВыбери опцию (1-4): ").strip()
        
        if choice == "1":
            batch_analyze_from_cli()
        elif choice == "2":
            import_wazzup_history()
        elif choice == "3":
            response = requests.get(f"{BASE_URL}/dashboard")
            if response.status_code == 200:
                stats = response.json()
                print(f"\n📊 СТАТИСТИКА СИСТЕМЫ:")
                print(f"   Всего диалогов: {stats['overview']['total_chats']}")
                print(f"   Активных чатов: {stats['overview']['active_chats']}")
                print(f"   Всего анализов: {stats['overview']['total_analyses']}")
                print(f"   Средняя оценка: {stats['overview']['average_score']:.1f}/50")
            else:
                print(f"❌ Ошибка получения статистики: {response.text}")
        elif choice == "4":
            print("👋 Выход...")
            break
        else:
            print("❌ Неверный выбор. Попробуй снова.")
        
        input("\nНажми Enter чтобы продолжить...")

if __name__ == "__main__":
    import time
    main_menu()