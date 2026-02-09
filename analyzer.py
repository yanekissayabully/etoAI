# import openai
# import json
# import os
# import asyncio
# import aiohttp
# from typing import List, Dict, Any, Optional
# import logging
# from dotenv import load_dotenv
# from datetime import datetime

# load_dotenv()

# logger = logging.getLogger(__name__)

# # Настройка OpenAI
# openai.api_key = os.getenv("OPENAI_API_KEY")

# # Кэш для промптов
# PROMPT_CACHE = {}

# def get_analysis_prompt() -> str:
#     """Возвращает промпт для анализа диалога"""
#     if "analysis" in PROMPT_CACHE:
#         return PROMPT_CACHE["analysis"]
    
#     prompt = """Ты - опытный супервайзер службы поддержки в мессенджерах. 
# Проанализируй диалог менеджера с клиентом в WhatsApp Business.

# КОНТЕКСТ:
# - Это бизнес-коммуникация в WhatsApp
# - Менеджер представляет компанию
# - Клиент ожидает профессионального и быстрого решения

# КРИТЕРИИ ОЦЕНКИ (поставь оценку от 1 до 10 по каждому):
# 1. ВЕЖЛИВОСТЬ И ЭМОЦИОНАЛЬНЫЙ ИНТЕЛЛЕКТ
#    - Использование приветствия и обращения по имени
#    - Эмпатия, понимание проблемы клиента
#    - Тон сообщений (дружелюбный/нейтральный/сухой)

# 2. ПРОФЕССИОНАЛИЗМ И ЯСНОСТЬ
#    - Четкость формулировок
#    - Точность информации
#    - Отсутствие грамматических ошибок

# 3. ПРОАКТИВНОСТЬ И РЕШЕНИЕ ПРОБЛЕМ
#    - Инициатива в решении (не ждет вопросов)
#    - Предложение конкретных решений
#    - Предвидение следующих шагов клиента

# 4. СКОРОСТЬ РЕАКЦИИ (по контексту диалога)
#    - Время между сообщениями (если указано)
#    - Оперативность ответов на вопросы
#    - Своевременное предоставление информации

# 5. WHATSAPP-СПЕЦИФИКА
#    - Уместность эмодзи и форматирования
#    - Длина сообщений (не слишком длинные)
#    - Использование быстрых ответов (если уместно)
#    - Структура диалога

# АНАЛИЗ ДОЛЖЕН ВКЛЮЧАТЬ:
# 1. Краткую выжимку диалога (2-3 предложения)
# 2. Оценку по критериям
# 3. Конкретные ошибки менеджера
# 4. Практические рекомендации по улучшению
# 5. Альтернативные формулировки для неудачных фраз
# 6. Общую оценку диалога (от 1 до 50, суммируя критерии)

# ФОРМАТ ОТВЕТА (строго JSON):
# {
#     "summary": "Краткая выжимка диалога",
#     "scores": {
#         "politeness": 0,
#         "professionalism": 0,
#         "proactivity": 0,
#         "response_speed": 0,
#         "whatsapp_effectiveness": 0
#     },
#     "total_score": 0,
#     "key_errors": ["конкретная ошибка 1", "ошибка 2"],
#     "whatsapp_specific_notes": ["заметка по WhatsApp 1", "заметка 2"],
#     "improvement_suggestions": ["практический совет 1", "совет 2"],
#     "alternative_phrases": {
#         "оригинальная фраза": "улучшенный вариант",
#         "еще фраза": "улучшенный вариант"
#     },
#     "emotional_tone": "нейтральный/позитивный/негативный",
#     "could_use_templates": true/false,
#     "template_suggestions": ["шаблон для...", "шаблон для..."]
# }

# Будь конкретным, конструктивным и давай практические советы, которые можно применить сразу."""
    
#     PROMPT_CACHE["analysis"] = prompt
#     return prompt

# def format_chat_for_ai(messages: List[Dict[str, Any]]) -> str:
#     """Форматирует диалог для отправки в ИИ"""
#     formatted_lines = [
#         "=" * 60,
#         "ДИАЛОГ МЕНЕДЖЕРА С КЛИЕНТОМ В WHATSAPP BUSINESS",
#         "=" * 60,
#         ""
#     ]
    
#     for i, msg in enumerate(messages, 1):
#         role = "👤 МЕНЕДЖЕР" if msg["role"] == "manager" else "👤 КЛИЕНТ"
#         text = msg["text"]
#         timestamp = msg.get("timestamp", "")
        
#         time_str = f" [{timestamp}]" if timestamp else ""
#         formatted_lines.append(f"{i}. {role}{time_str}: {text}")
    
#     formatted_lines.extend([
#         "",
#         "=" * 60,
#         "ПРОСЬБА: Проанализируй вышеуказанный диалог по критериям."
#     ])
    
#     return "\n".join(formatted_lines)

# def analyze_chat(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
#     """
#     Анализирует диалог менеджера с клиентом через GPT
#     Возвращает структурированный отчет
#     """
#     try:
#         # Проверяем API ключ
#         if not openai.api_key:
#             logger.error("❌ OpenAI API key not configured")
#             return create_error_response("OpenAI API key not configured")
        
#         # Форматируем диалог
#         formatted_chat = format_chat_for_ai(messages)
        
#         # Получаем промпт
#         system_prompt = get_analysis_prompt()
        
#         logger.info(f"🤖 Starting AI analysis for {len(messages)} messages")
        
#         # Запрос к OpenAI
#         response = openai.ChatCompletion.create(
#             model="gpt-3.5-turbo-1106",  # Хороший баланс цена/качество
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": formatted_chat}
#             ],
#             temperature=0.3,  # Более консервативные оценки
#             max_tokens=1500,
#             response_format={"type": "json_object"}
#         )
        
#         # Парсим ответ
#         result = json.loads(response.choices[0].message.content)
        
#         # Валидируем и обогащаем результат
#         validated_result = validate_and_enrich_analysis(result, messages)
        
#         logger.info(f"✅ Analysis completed. Total score: {validated_result.get('total_score', 0)}")
        
#         return validated_result
        
#     except openai.error.AuthenticationError:
#         logger.error("❌ OpenAI authentication failed. Check API key.")
#         return create_error_response("OpenAI authentication failed")
#     except openai.error.RateLimitError:
#         logger.error("❌ OpenAI rate limit exceeded")
#         return create_error_response("Rate limit exceeded. Please try again later.")
#     except openai.error.APIError as e:
#         logger.error(f"❌ OpenAI API error: {e}")
#         return create_error_response(f"OpenAI API error: {str(e)}")
#     except json.JSONDecodeError:
#         logger.error("❌ Failed to parse OpenAI response as JSON")
#         return create_error_response("Failed to parse AI response")
#     except Exception as e:
#         logger.error(f"❌ Unexpected error in analysis: {e}")
#         return create_error_response(f"Analysis error: {str(e)}")

# def validate_and_enrich_analysis(analysis: Dict[str, Any], messages: List[Dict]) -> Dict[str, Any]:
#     """Валидация и обогащение результата анализа"""
#     # Базовые проверки
#     if not isinstance(analysis, dict):
#         analysis = {}
    
#     # Убедимся что есть обязательные поля
#     required_fields = ["summary", "scores", "total_score", "key_errors"]
#     for field in required_fields:
#         if field not in analysis:
#             analysis[field] = "" if field == "summary" else [] if field == "key_errors" else {}
    
#     # Валидируем scores
#     if "scores" not in analysis or not isinstance(analysis["scores"], dict):
#         analysis["scores"] = {}
    
#     # Убедимся что total_score - число
#     if not isinstance(analysis.get("total_score"), (int, float)):
#         # Вычисляем из scores если есть
#         scores = analysis.get("scores", {})
#         if scores:
#             analysis["total_score"] = sum(v for v in scores.values() if isinstance(v, (int, float)))
#         else:
#             analysis["total_score"] = 0
    
#     # Добавляем метаданные
#     analysis["analysis_metadata"] = {
#         "model": "gpt-4o-mini",
#         "analyzed_at": datetime.now().isoformat(),
#         "message_count": len(messages),
#         "manager_messages": len([m for m in messages if m["role"] == "manager"]),
#         "client_messages": len([m for m in messages if m["role"] == "client"]),
#         "chat_duration": calculate_chat_duration(messages)
#     }
    
#     # Вычисляем оценку по 5-балльной шкале для удобства
#     total_score = analysis["total_score"]
#     if total_score > 0:
#         analysis["score_5_point"] = round((total_score / 50) * 5, 1)
#         analysis["rating"] = get_rating_text(total_score)
    
#     return analysis

# def calculate_chat_duration(messages: List[Dict]) -> Optional[str]:
#     """Вычисляет продолжительность диалога"""
#     if len(messages) < 2:
#         return None
    
#     try:
#         # Пытаемся получить временные метки
#         timestamps = []
#         for msg in messages:
#             ts = msg.get("timestamp")
#             if ts:
#                 if isinstance(ts, str):
#                     dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
#                 elif isinstance(ts, (int, float)):
#                     dt = datetime.fromtimestamp(ts)
#                 else:
#                     continue
#                 timestamps.append(dt)
        
#         if len(timestamps) >= 2:
#             duration = max(timestamps) - min(timestamps)
            
#             # Форматируем
#             hours, remainder = divmod(duration.seconds, 3600)
#             minutes, seconds = divmod(remainder, 60)
            
#             if hours > 0:
#                 return f"{hours}ч {minutes}м"
#             elif minutes > 0:
#                 return f"{minutes}м {seconds}с"
#             else:
#                 return f"{seconds}с"
#     except:
#         pass
    
#     return None

# def get_rating_text(score: float) -> str:
#     """Возвращает текстовую оценку по числовому баллу"""
#     if score >= 45:
#         return "Отлично! 🎯"
#     elif score >= 35:
#         return "Хорошо 👍"
#     elif score >= 25:
#         return "Удовлетворительно 👌"
#     elif score >= 15:
#         return "Требует улучшения ⚠️"
#     else:
#         return "Критично нуждается в улучшении 🚨"

# def create_error_response(error_message: str) -> Dict[str, Any]:
#     """Создает ответ об ошибке"""
#     return {
#         "summary": f"Ошибка анализа: {error_message}",
#         "scores": {
#             "politeness": 0,
#             "professionalism": 0,
#             "proactivity": 0,
#             "response_speed": 0,
#             "whatsapp_effectiveness": 0
#         },
#         "total_score": 0,
#         "key_errors": [f"Ошибка анализа: {error_message}"],
#         "improvement_suggestions": ["Проверьте подключение к OpenAI API"],
#         "error": True,
#         "error_message": error_message,
#         "analysis_metadata": {
#             "error": True,
#             "analyzed_at": datetime.now().isoformat()
#         }
#     }

# def print_analysis_pretty(analysis: Dict[str, Any], show_details: bool = True):
#     """Красивый вывод анализа в консоль"""
#     print("\n" + "="*70)
#     print("🤖 АНАЛИЗ ДИАЛОГА WHATSAPP BUSINESS")
#     print("="*70)
    
#     # Основная информация
#     summary = analysis.get("summary", "Нет данных")
#     total_score = analysis.get("total_score", 0)
#     score_5 = analysis.get("score_5_point", 0)
#     rating = analysis.get("rating", "")
    
#     print(f"\n📋 ВЫЖИМКА: {summary}")
#     print(f"🎯 ОБЩАЯ ОЦЕНКА: {total_score}/50 ({score_5}/5) {rating}")
    
#     if show_details and "scores" in analysis:
#         print("\n📊 ОЦЕНКА ПО КРИТЕРИЯМ:")
#         scores = analysis["scores"]
#         for criterion, score in scores.items():
#             if isinstance(score, (int, float)):
#                 bar = "█" * int(score / 2) + "░" * (5 - int(score / 2))
#                 criterion_name = {
#                     "politeness": "Вежливость",
#                     "professionalism": "Профессионализм",
#                     "proactivity": "Проактивность",
#                     "response_speed": "Скорость реакции",
#                     "whatsapp_effectiveness": "WhatsApp-эффективность"
#                 }.get(criterion, criterion)
                
#                 print(f"  {criterion_name:25} {score:2}/10 {bar}")
    
#     if show_details and analysis.get("key_errors"):
#         print("\n❌ КЛЮЧЕВЫЕ ОШИБКИ:")
#         for error in analysis["key_errors"][:5]:  # Показываем первые 5
#             print(f"  • {error}")
    
#     if show_details and analysis.get("improvement_suggestions"):
#         print("\n💡 СОВЕТЫ ПО УЛУЧШЕНИЮ:")
#         for suggestion in analysis["improvement_suggestions"][:5]:
#             print(f"  • {suggestion}")
    
#     if show_details and analysis.get("whatsapp_specific_notes"):
#         print("\n📱 WHATSAPP-ОСОБЕННОСТИ:")
#         for note in analysis["whatsapp_specific_notes"][:3]:
#             print(f"  • {note}")
    
#     if show_details and analysis.get("alternative_phrases"):
#         print("\n🔄 АЛЬТЕРНАТИВНЫЕ ФОРМУЛИРОВКИ:")
#         phrases = analysis["alternative_phrases"]
#         for original, alternative in list(phrases.items())[:3]:
#             print(f"  Было: \"{original[:60]}{'...' if len(original) > 60 else ''}\"")
#             print(f"  Лучше: \"{alternative[:60]}{'...' if len(alternative) > 60 else ''}\"")
#             print()
    
#     # Метаданные
#     meta = analysis.get("analysis_metadata", {})
#     if meta:
#         print("\n📈 МЕТАДАННЫЕ:")
#         print(f"  Сообщений: {meta.get('message_count', 0)}")
#         print(f"  Сообщений менеджера: {meta.get('manager_messages', 0)}")
#         if meta.get('chat_duration'):
#             print(f"  Продолжительность: {meta['chat_duration']}")
#         print(f"  Модель: {meta.get('model', 'N/A')}")
    
#     print("="*70 + "\n")

# async def analyze_chat_async(chat_id: str, messages: List[Dict], task_id: str = None):
#     """Асинхронный анализ диалога"""
#     from main import analyses_db, logger
    
#     try:
#         logger.info(f"🤖 Starting async analysis for chat {chat_id}")
        
#         # Здесь можно добавить логику для фонового анализа
#         # Пока используем синхронную версию
#         result = analyze_chat(messages)
        
#         # Сохраняем результат
#         analyses_db[chat_id] = {
#             **result,
#             "chat_id": chat_id,
#             "analyzed_at": datetime.now().isoformat(),
#             "task_id": task_id,
#             "async": True
#         }
        
#         logger.info(f"✅ Async analysis completed for chat {chat_id}")
        
#     except Exception as e:
#         logger.error(f"❌ Async analysis failed for chat {chat_id}: {e}")
        
#         # Сохраняем ошибку
#         analyses_db[chat_id] = {
#             "error": True,
#             "error_message": str(e),
#             "chat_id": chat_id,
#             "analyzed_at": datetime.now().isoformat()
#         }

# # Тестовые данные для разработки
# TEST_CHAT = [
#     {"role": "client", "text": "Добрый день! Подскажите, когда приедет мой заказ #12345?"},
#     {"role": "manager", "text": "Здравствуйте! Проверяю информацию...", "timestamp": "2024-01-20T10:05:00"},
#     {"role": "manager", "text": "Ваш заказ отправили вчера. Трек-номер: RA987654321RU", "timestamp": "2024-01-20T10:07:00"},
#     {"role": "client", "text": "Спасибо! А примерные сроки доставки?", "timestamp": "2024-01-20T10:08:00"},
#     {"role": "manager", "text": "5-7 рабочих дней. Отслеживайте по треку", "timestamp": "2024-01-20T10:09:00"},
#     {"role": "client", "text": "Понял, спасибо за помощь!", "timestamp": "2024-01-20T10:10:00"}
# ]

# if __name__ == "__main__":
#     # Тестирование анализатора
#     print("🧪 Тестируем анализатор...")
#     result = analyze_chat(TEST_CHAT)
#     print_analysis_pretty(result)
    
#     # Сохраняем тестовый результат
#     with open("test_analysis.json", "w") as f:
#         json.dump(result, f, ensure_ascii=False, indent=2)
    
#     print("✅ Тест завершен. Результат сохранен в test_analysis.json")


import openai
import json
import os
import logging
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Настройка OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # По умолчанию gpt-4o-mini

def analyze_chat(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Анализирует диалог менеджера с клиентом через GPT-4o-mini
    """
    try:
        # Проверяем API ключ
        if not OPENAI_API_KEY:
            logger.error("❌ OpenAI API key not configured")
            return create_error_response("OpenAI API key not configured")
        
        # Форматируем диалог для ИИ
        formatted_chat = format_chat_for_ai(messages)
        
        # Улучшенный промпт для анализа WhatsApp диалогов
        system_prompt = """Ты - старший супервайзер службы поддержки с 10-летним опытом.
Тебе нужно проанализировать диалог менеджера с клиентом в WhatsApp Business.

АНАЛИЗИРУЙ ПО ЭТИМ КРИТЕРИЯМ (оценка от 1 до 10):

1. 🎭 ВЕЖЛИВОСТЬ И ЭМОЦИОНАЛЬНЫЙ ИНТЕЛЛЕКТ
   - Приветствие и обращение по имени
   - Эмпатия и понимание проблемы
   - Тон сообщений

2. 💼 ПРОФЕССИОНАЛИЗМ
   - Четкость формулировок
   - Точность информации
   - Грамматика и орфография

3. ⚡ ПРОАКТИВНОСТЬ
   - Инициатива в решении
   - Предложение решений
   - Предвидение вопросов клиента

4. ⏱️ ОПЕРАТИВНОСТЬ (по контексту диалога)
   - Время между репликами
   - Быстрота ответов
   - Своевременность информации

5. 📱 WHATSAPP-ЭФФЕКТИВНОСТЬ
   - Уместность эмодзи
   - Длина сообщений (оптимально 1-3 предложения)
   - Структурированность ответов
   - Использование быстрых ответов (где уместно)

ВОЗВРАЩАЙ ОТВЕТ В СТРОГОМ JSON ФОРМАТЕ:
{
    "summary": "Краткая выжимка диалога (2-3 предложения)",
    "scores": {
        "politeness": 0,
        "professionalism": 0,
        "proactivity": 0,
        "response_speed": 0,
        "whatsapp_effectiveness": 0
    },
    "total_score": 0,
    "key_errors": ["конкретная ошибка 1", "ошибка 2"],
    "improvement_suggestions": ["практический совет 1", "совет 2"],
    "alternative_phrases": {
        "неудачная фраза": "улучшенный вариант"
    },
    "emotional_tone": "нейтральный/позитивный/негативный",
    "use_templates_score": 0-10,
    "overall_verdict": "отлично/хорошо/удовлетворительно/плохо"
}

Будь КОНКРЕТНЫМ и давай ПРАКТИЧЕСКИЕ советы. Указывай конкретные фразы из диалога."""
        
        logger.info(f"🤖 Начинаю анализ {len(messages)} сообщений с моделью {OPENAI_MODEL}...")
        
        # Создаем клиент OpenAI
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Отправляем запрос к GPT-4o-mini
        response = client.chat.completions.create(
            model=OPENAI_MODEL,  # Используем gpt-4o-mini
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": formatted_chat}
            ],
            temperature=0.2,  # Низкая температура для более консистентных оценок
            max_tokens=1500,
            response_format={"type": "json_object"}
        )
        
        # Парсим ответ
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        # Добавляем метаданные и вычисляем общую оценку
        result = enrich_analysis_result(result, messages)
        
        logger.info(f"✅ Анализ завершен! Оценка: {result.get('total_score', 0)}/50")
        return result
        
    except openai.APIConnectionError as e:
        logger.error(f"❌ Ошибка подключения к OpenAI: {e}")
        return create_error_response("Ошибка подключения к OpenAI. Проверь интернет.")
    except openai.RateLimitError as e:
        logger.error(f"❌ Превышен лимит запросов: {e}")
        return create_error_response("Превышен лимит запросов OpenAI. Попробуй через минуту.")
    except openai.AuthenticationError as e:
        logger.error(f"❌ Ошибка аутентификации: {e}")
        return create_error_response("Неверный API ключ OpenAI. Проверь .env файл.")
    except openai.BadRequestError as e:
        logger.error(f"❌ Неверный запрос: {e}")
        return create_error_response(f"Ошибка в запросе: {str(e)[:100]}")
    except Exception as e:
        logger.error(f"❌ Неизвестная ошибка: {e}")
        return create_error_response(f"Ошибка анализа: {str(e)[:100]}")

def format_chat_for_ai(messages: List[Dict[str, Any]]) -> str:
    """Форматирует диалог для отправки в ИИ с контекстом WhatsApp"""
    lines = [
        "=" * 60,
        "WHATSDIAG: АНАЛИЗ ДИАЛОГА В WHATSAPP BUSINESS",
        "=" * 60,
        f"Всего сообщений: {len(messages)}",
        f"Сообщений менеджера: {sum(1 for m in messages if m['role'] == 'manager')}",
        f"Сообщений клиента: {sum(1 for m in messages if m['role'] == 'client')}",
        "=" * 60,
        ""
    ]
    
    for i, msg in enumerate(messages, 1):
        role_emoji = "👨‍💼" if msg["role"] == "manager" else "👤"
        role_text = "МЕНЕДЖЕР" if msg["role"] == "manager" else "КЛИЕНТ"
        text = msg["text"]
        
        lines.append(f"{i}. {role_emoji} {role_text}:")
        lines.append(f"   \"{text}\"")
        lines.append("")
    
    lines.append("=" * 60)
    lines.append("ПРОАНАЛИЗИРУЙ ЭТОТ ДИАЛОГ ПО КРИТЕРИЯМ ВЫШЕ")
    
    return "\n".join(lines)

def enrich_analysis_result(result: Dict[str, Any], messages: List[Dict]) -> Dict[str, Any]:
    """Добавляет метаданные и вычисляет итоговые оценки"""
    
    # Вычисляем общую оценку если не указана
    if "total_score" not in result or result["total_score"] == 0:
        scores = result.get("scores", {})
        if scores and all(isinstance(v, (int, float)) for v in scores.values()):
            result["total_score"] = sum(scores.values())
        else:
            result["total_score"] = 25  # Средняя оценка по умолчанию
    
    # Определяем вердикт по общей оценке
    total_score = result["total_score"]
    if total_score >= 45:
        verdict = "Отлично! 🎯"
        grade = "A"
    elif total_score >= 35:
        verdict = "Хорошо 👍"
        grade = "B"
    elif total_score >= 25:
        verdict = "Удовлетворительно 👌"
        grade = "C"
    elif total_score >= 15:
        verdict = "Требует улучшения ⚠️"
        grade = "D"
    else:
        verdict = "Критически плохо 🚨"
        grade = "F"
    
    # Добавляем метаданные
    result["analysis_metadata"] = {
        "model_used": OPENAI_MODEL,
        "analyzed_at": datetime.now().isoformat(),
        "message_count": len(messages),
        "manager_messages": sum(1 for m in messages if m["role"] == "manager"),
        "client_messages": sum(1 for m in messages if m["role"] == "client"),
        "grade": grade,
        "score_percentage": int((total_score / 50) * 100)
    }
    
    result["verdict"] = verdict
    result["grade"] = grade
    
    # Обеспечиваем наличие всех полей
    if "key_errors" not in result:
        result["key_errors"] = []
    if "improvement_suggestions" not in result:
        result["improvement_suggestions"] = []
    if "alternative_phrases" not in result:
        result["alternative_phrases"] = {}
    if "emotional_tone" not in result:
        result["emotional_tone"] = "нейтральный"
    
    return result

def create_error_response(error_message: str) -> Dict[str, Any]:
    """Создает ответ об ошибке"""
    return {
        "summary": f"Ошибка анализа: {error_message}",
        "scores": {
            "politeness": 0,
            "professionalism": 0,
            "proactivity": 0,
            "response_speed": 0,
            "whatsapp_effectiveness": 0
        },
        "total_score": 0,
        "key_errors": [f"Ошибка системы: {error_message}"],
        "improvement_suggestions": ["Перезапустите анализ", "Проверьте подключение к интернету"],
        "alternative_phrases": {},
        "emotional_tone": "нейтральный",
        "verdict": "Ошибка анализа 🚫",
        "grade": "E",
        "error": True,
        "error_message": error_message,
        "analysis_metadata": {
            "error": True,
            "analyzed_at": datetime.now().isoformat(),
            "model_used": OPENAI_MODEL
        }
    }

def print_analysis_pretty(analysis: Dict[str, Any]):
    """Красивый вывод анализа в консоль"""
    print("\n" + "="*70)
    print("🤖 АНАЛИЗ ДИАЛОГА WHATSAPP (GPT-4o-mini)")
    print("="*70)
    
    if analysis.get("error"):
        print(f"❌ ОШИБКА: {analysis.get('error_message', 'Неизвестная ошибка')}")
        print("="*70)
        return
    
    # Основная информация
    print(f"📋 ВЫЖИМКА: {analysis.get('summary', 'Нет данных')}")
    print(f"🎯 ОБЩАЯ ОЦЕНКА: {analysis.get('total_score', 0)}/50")
    print(f"⭐ ВЕРДИКТ: {analysis.get('verdict', '')}")
    print(f"🏆 ОЦЕНКА: {analysis.get('grade', '')}")
    
    # Оценки по критериям
    if "scores" in analysis:
        print("\n📊 ОЦЕНКА ПО КРИТЕРИЯМ:")
        scores = analysis["scores"]
        
        for criterion, score in scores.items():
            if isinstance(score, (int, float)):
                # Прогресс-бар
                filled = int(score / 2)
                bar = "█" * filled + "░" * (5 - filled)
                
                # Русские названия критериев
                names = {
                    "politeness": "🎭 Вежливость",
                    "professionalism": "💼 Профессионализм", 
                    "proactivity": "⚡ Проактивность",
                    "response_speed": "⏱️ Оперативность",
                    "whatsapp_effectiveness": "📱 WhatsApp-эффективность"
                }
                
                criterion_name = names.get(criterion, criterion)
                print(f"  {criterion_name:25} {score:2}/10 {bar}")
    
    # Ошибки
    if analysis.get("key_errors"):
        print(f"\n❌ КЛЮЧЕВЫЕ ОШИБКИ ({len(analysis['key_errors'])}):")
        for error in analysis["key_errors"][:3]:  # Показываем первые 3
            print(f"  • {error}")
    
    # Советы
    if analysis.get("improvement_suggestions"):
        print(f"\n💡 СОВЕТЫ ПО УЛУЧШЕНИЮ ({len(analysis['improvement_suggestions'])}):")
        for suggestion in analysis["improvement_suggestions"][:3]:
            print(f"  • {suggestion}")
    
    # Альтернативные фразы
    if analysis.get("alternative_phrases"):
        phrases = analysis["alternative_phrases"]
        if phrases:
            print(f"\n🔄 АЛЬТЕРНАТИВНЫЕ ФРАЗЫ ({len(phrases)}):")
            for original, alternative in list(phrases.items())[:2]:
                print(f"  Было: \"{original[:50]}{'...' if len(original) > 50 else ''}\"")
                print(f"  Лучше: \"{alternative[:50]}{'...' if len(alternative) > 50 else ''}\"")
                print()
    
    # Метаданные
    meta = analysis.get("analysis_metadata", {})
    if meta:
        print("\n📈 МЕТАДАННЫЕ:")
        print(f"  Модель: {meta.get('model_used', 'N/A')}")
        print(f"  Сообщений: {meta.get('message_count', 0)}")
        print(f"  Менеджер: {meta.get('manager_messages', 0)} сообщений")
        print(f"  Клиент: {meta.get('client_messages', 0)} сообщений")
        print(f"  Процент: {meta.get('score_percentage', 0)}%")
    
    print("="*70)

# Тест анализатора
if __name__ == "__main__":
    print("🧪 ТЕСТИРУЮ АНАЛИЗАТОР С GPT-4o-mini")
    print("=" * 50)
    
    test_dialog = [
        {"role": "client", "text": "Добрый день! Не могу найти свой заказ #78910 в системе"},
        {"role": "manager", "text": "Привет. Номер заказа?", "timestamp": "2024-01-20T10:05:00"},
        {"role": "client", "text": "78910", "timestamp": "2024-01-20T10:06:00"},
        {"role": "manager", "text": "Проверил. Отправили вчера.", "timestamp": "2024-01-20T10:08:00"},
        {"role": "client", "text": "А трек номер есть? Когда примерно придет?", "timestamp": "2024-01-20T10:09:00"},
        {"role": "manager", "text": "Трек: RA123456789RU. Ждите.", "timestamp": "2024-01-20T10:10:00"}
    ]
    
    result = analyze_chat(test_dialog)
    print_analysis_pretty(result)
    
    # Сохраняем тестовый результат
    with open("test_gpt4omini_analysis.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("✅ Тест завершен. Результат сохранен в test_gpt4omini_analysis.json")