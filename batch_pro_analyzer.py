import requests
import json
import csv
import sys
from datetime import datetime, timedelta
import pandas as pd

BASE_URL = "http://localhost:8000"

def print_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█'):
    """Печатает прогресс-бар"""
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r')
    if iteration == total:
        print()

def batch_pro_analyze_cli():
    """Утилита для массового профессионального анализа"""
    
    print("🔍 ПРОФЕССИОНАЛЬНЫЙ МАССОВЫЙ АНАЛИЗ (ОКК)")
    print("=" * 60)
    
    # Проверяем сервер
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Сервер не отвечает")
            return
    except:
        print("❌ Сервер не запущен")
        print("👉 Запусти: python main_pro.py")
        return
    
    print("✅ Сервер работает")
    
    # Получаем список чатов
    print("\n📂 Получаю список диалогов...")
    response = requests.get(f"{BASE_URL}/chats?limit=100")
    
    if response.status_code != 200:
        print(f"❌ Ошибка: {response.text}")
        return
    
    chats_data = response.json()
    chats = chats_data.get("chats", [])
    total_chats = chats_data.get("total", 0)
    
    print(f"✅ Найдено {total_chats} диалогов (показано {len(chats)})")
    
    if not chats:
        print("❌ Нет диалогов для анализа")
        return
    
    # Меню фильтров
    print("\n🎯 ФИЛЬТРЫ АНАЛИЗА")
    print("1. Все диалоги")
    print("2. Только без анализа")
    print("3. Только конкретного менеджера")
    print("4. Только за период")
    print("5. Только с минимумом сообщений")
    
    choice = input("\nВыбери опцию (1-5): ").strip()
    
    filtered_chats = []
    
    if choice == "1":
        filtered_chats = chats
    elif choice == "2":
        filtered_chats = [c for c in chats if not c.get("has_pro_analysis")]
    elif choice == "3":
        # Показываем менеджеров
        managers = set(c.get("manager_id", "unknown") for c in chats)
        print(f"\n📋 Менеджеры: {', '.join(managers)}")
        manager_id = input("Введи ID менеджера: ").strip()
        filtered_chats = [c for c in chats if c.get("manager_id") == manager_id]
    elif choice == "4":
        start_date = input("Начальная дата (YYYY-MM-DD): ").strip()
        end_date = input("Конечная дата (YYYY-MM-DD): ").strip()
        
        for chat in chats:
            chat_date = datetime.fromisoformat(chat["created_at"].replace('Z', '+00:00'))
            
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
                if chat_date < start_dt:
                    continue
            
            if end_date:
                end_dt = datetime.fromisoformat(end_date)
                if chat_date > end_dt:
                    continue
            
            filtered_chats.append(chat)
    elif choice == "5":
        min_msgs = input("Минимум сообщений: ").strip()
        try:
            min_msgs = int(min_msgs)
            filtered_chats = [c for c in chats if c.get("message_count", 0) >= min_msgs]
        except:
            print("❌ Неверное число")
            return
    else:
        print("❌ Неверный выбор")
        return
    
    if not filtered_chats:
        print("❌ Нет диалогов по выбранным критериям")
        return
    
    print(f"\n📊 Будет проанализировано: {len(filtered_chats)} диалогов")
    
    # Подтверждение
    confirm = input("\nЗапустить массовый анализ? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Отменено")
        return
    
    # Запускаем массовый анализ
    print(f"\n🚀 Запускаю профессиональный анализ...")
    
    chat_ids = [c["id"] for c in filtered_chats]
    
    # Используем API для массового анализа
    response = requests.post(
        f"{BASE_URL}/analyze/pro/batch",
        params={
            "limit": len(chat_ids),
            "force": False
        },
        timeout=300  # 5 минут таймаут
    )
    
    if response.status_code == 200:
        result = response.json()
        
        successful = result.get("successful", 0)
        failed = result.get("failed", 0)
        avg_score = result.get("average_score", 0)
        
        print(f"\n✅ Анализ завершен!")
        print(f"   Успешно: {successful}")
        print(f"   Ошибки: {failed}")
        print(f"   Средний счет: {avg_score:.1f}/100")
        
        # Экспорт результатов
        export_choice = input("\nЭкспортировать результаты в CSV? (y/n): ").strip().lower()
        if export_choice == 'y':
            export_response = requests.get(f"{BASE_URL}/export/csv")
            
            if export_response.status_code == 200:
                # Сохраняем файл
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"okc_batch_analysis_{timestamp}.csv"
                
                with open(filename, 'w', encoding='utf-8-sig') as f:
                    f.write(export_response.text)
                
                print(f"✅ Результаты экспортированы в {filename}")
                
                # Показываем предпросмотр
                try:
                    df = pd.read_csv(filename, sep=';')
                    print(f"\n📊 ПРЕДПРОСМОТР (первые 5 строк):")
                    print(df.head().to_string(index=False))
                except:
                    pass
            else:
                print(f"❌ Ошибка экспорта: {export_response.text}")
        
        # Показываем дашборд
        print(f"\n📈 СТАТИСТИКА АНАЛИЗА:")
        dashboard_response = requests.get(f"{BASE_URL}/dashboard/pro")
        
        if dashboard_response.status_code == 200:
            dashboard = dashboard_response.json()
            
            print(f"   Всего анализов: {dashboard['overview']['total_analyses']}")
            print(f"   Средний счет: {dashboard['overview']['average_score']:.1f}")
            print(f"   Покрытие: {dashboard['overview']['coverage_percentage']}%")
            
            # Топ менеджеров
            print(f"\n🏆 ТОП МЕНЕДЖЕРОВ:")
            for i, manager in enumerate(dashboard['top_managers'][:3], 1):
                print(f"   {i}. {manager['manager']}: {manager['average_score']} ({manager['chat_count']} чатов)")
        
        return result
    else:
        print(f"❌ Ошибка массового анализа: {response.text}")
        return None

def analyze_single_pro_chat():
    """Анализ одного чата"""
    print("\n🔍 АНАЛИЗ ОДНОГО ЧАТА")
    print("=" * 40)
    
    chat_id = input("Введи ID чата: ").strip()
    
    if not chat_id:
        print("❌ ID чата не указан")
        return
    
    print(f"\n🧠 Анализирую чат {chat_id}...")
    
    response = requests.post(
        f"{BASE_URL}/analyze/pro/{chat_id}",
        params={"force": True},
        timeout=120
    )
    
    if response.status_code == 200:
        result = response.json()
        score = result.get("score", 0)
        
        print(f"✅ Анализ завершен!")
        print(f"   Счет: {score}/100")
        
        # Показываем табличную строку
        table_row = result.get("table_row", {})
        print(f"\n📋 ТАБЛИЧНАЯ СТРОКА:")
        
        for key, value in table_row.items():
            if key in ["summary_score", "chat_id", "manager", "final_status"]:
                print(f"   {key}: {value}")
        
        # Показать рекомендации
        analysis = result.get("analysis", {})
        recs = analysis.get("l6_recommendations", {})
        
        if recs.get("done_well"):
            print(f"\n✅ ЧТО СДЕЛАНО ХОРОШО:")
            for item in recs["done_well"]:
                print(f"   • {item}")
        
        if recs.get("improvements"):
            print(f"\n🔧 ЧТО МОЖНО УЛУЧШИТЬ:")
            for item in recs["improvements"]:
                print(f"   • {item}")
        
        return result
    else:
        print(f"❌ Ошибка анализа: {response.text}")
        return None

def export_all_to_excel():
    """Экспорт всех анализов в Excel"""
    print("\n📤 ЭКСПОРТ В EXCEL")
    print("=" * 40)
    
    response = requests.get(f"{BASE_URL}/export/csv")
    
    if response.status_code == 200:
        # Сохраняем CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"okc_full_export_{timestamp}.csv"
        excel_filename = f"okc_full_export_{timestamp}.xlsx"
        
        with open(csv_filename, 'w', encoding='utf-8-sig') as f:
            f.write(response.text)
        
        # Конвертируем в Excel
        try:
            df = pd.read_csv(csv_filename, sep=';')
            df.to_excel(excel_filename, index=False)
            
            print(f"✅ Экспорт завершен!")
            print(f"   CSV: {csv_filename}")
            print(f"   Excel: {excel_filename}")
            print(f"   Строк: {len(df)}")
            
            # Показываем статистику
            if 'summary_score' in df.columns:
                print(f"\n📊 СТАТИСТИКА:")
                print(f"   Средний счет: {df['summary_score'].mean():.1f}")
                print(f"   Максимальный: {df['summary_score'].max():.1f}")
                print(f"   Минимальный: {df['summary_score'].min():.1f}")
                
                # Распределение
                excellent = len(df[df['summary_score'] >= 80])
                good = len(df[(df['summary_score'] >= 60) & (df['summary_score'] < 80)])
                average = len(df[(df['summary_score'] >= 40) & (df['summary_score'] < 60)])
                poor = len(df[df['summary_score'] < 40])
                
                print(f"\n   РАСПРЕДЕЛЕНИЕ:")
                print(f"   Отлично (80-100): {excellent}")
                print(f"   Хорошо (60-79): {good}")
                print(f"   Удовлетворительно (40-59): {average}")
                print(f"   Требует улучшения (0-39): {poor}")
        
        except Exception as e:
            print(f"❌ Ошибка конвертации в Excel: {e}")
    
    else:
        print(f"❌ Ошибка экспорта: {response.text}")

def show_dashboard():
    """Показать дашборд"""
    print("\n📊 ПРОФЕССИОНАЛЬНЫЙ ДАШБОРД")
    print("=" * 50)
    
    response = requests.get(f"{BASE_URL}/dashboard/pro")
    
    if response.status_code == 200:
        dashboard = response.json()
        
        print(f"📈 ОБЗОР:")
        print(f"   Всего чатов: {dashboard['overview']['total_chats']}")
        print(f"   Проанализировано: {dashboard['overview']['total_analyses']}")
        print(f"   Покрытие: {dashboard['overview']['coverage_percentage']}%")
        print(f"   Средний счет: {dashboard['overview']['average_score']:.1f}/100")
        
        print(f"\n🎯 РАСПРЕДЕЛЕНИЕ ОЦЕНОК:")
        dist = dashboard['score_distribution']
        print(f"   Отлично (80-100): {dist['excellent']}")
        print(f"   Хорошо (60-79): {dist['good']}")
        print(f"   Удовлетворительно (40-59): {dist['average']}")
        print(f"   Требует улучшения (0-39): {dist['poor']}")
        
        print(f"\n🏆 ТОП МЕНЕДЖЕРОВ:")
        for i, manager in enumerate(dashboard['top_managers'][:3], 1):
            print(f"   {i}. {manager['manager']}: {manager['average_score']} ({manager['chat_count']} чатов)")
        
        print(f"\n🚨 ЧАСТЫЕ ПРОБЛЕМЫ:")
        for i, problem in enumerate(dashboard['common_problems'][:3], 1):
            print(f"   {i}. {problem['problem']}: {problem['count']} раз")
    
    else:
        print(f"❌ Ошибка получения дашборда: {response.text}")

def main_menu():
    """Главное меню"""
    while True:
        print("\n" + "="*60)
        print("🛠️  ПРОФЕССИОНАЛЬНЫЙ АНАЛИЗАТОР ОКК v2.0")
        print("="*60)
        print("1. 🔍 Массовый профессиональный анализ")
        print("2. 👤 Анализ одного чата")
        print("3. 📤 Экспорт всех данных в Excel")
        print("4. 📊 Показать дашборд")
        print("5. 📋 Список чатов")
        print("6. 🚪 Выход")
        
        choice = input("\nВыбери опцию (1-6): ").strip()
        
        if choice == "1":
            batch_pro_analyze_cli()
        elif choice == "2":
            analyze_single_pro_chat()
        elif choice == "3":
            export_all_to_excel()
        elif choice == "4":
            show_dashboard()
        elif choice == "5":
            response = requests.get(f"{BASE_URL}/chats?limit=20")
            if response.status_code == 200:
                chats = response.json().get("chats", [])
                print(f"\n📋 ПОСЛЕДНИЕ {len(chats)} ЧАТОВ:")
                for chat in chats:
                    has_analysis = "✅" if chat.get("has_pro_analysis") else "❌"
                    score = f"{chat.get('pro_score')}/100" if chat.get('pro_score') else "—"
                    print(f"   {has_analysis} {chat['id']}: {chat['client_number']} (менеджер: {chat['manager_id']}) {score}")
        elif choice == "6":
            print("\n👋 Выход...")
            break
        else:
            print("❌ Неверный выбор")
        
        input("\nНажми Enter чтобы продолжить...")

if __name__ == "__main__":
    main_menu()