# analyzer_fixed.py - РАБОЧАЯ ВЕРСИЯ БЕЗ ПРОБЛЕМ С КОДИРОВКОЙ
import openai
import json
import os
import logging
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Настройки
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

def clean_text(text: str) -> str:
    """Очищает текст от всех не-ASCII символов"""
    if not isinstance(text, str):
        return str(text)
    
    # Удаляем все не-ASCII символы
    import re
    cleaned = re.sub(r'[^\x00-\x7F]+', ' ', text)
    # Заменяем проблемные символы
    cleaned = cleaned.replace('"', "'").replace('\\', '/')
    # Удаляем лишние пробелы
    cleaned = ' '.join(cleaned.split())
    return cleaned

def analyze_chat(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """АНАЛИЗАТОР - РАБОЧАЯ ВЕРСИЯ"""
    try:
        # Проверка API ключа
        if not OPENAI_API_KEY:
            return {
                "error": True,
                "error_message": "OpenAI API key not configured",
                "summary": "API key missing",
                "total_score": 0
            }
        
        logger.info(f"Analyzing {len(messages)} messages...")
        
        # Очищаем все сообщения
        cleaned_messages = []
        for msg in messages:
            cleaned_msg = msg.copy()
            cleaned_msg["text"] = clean_text(msg.get("text", ""))
            cleaned_messages.append(cleaned_msg)
        
        # Форматируем диалог ПРОСТО
        dialog_lines = ["CHAT ANALYSIS REQUEST:", ""]
        for i, msg in enumerate(cleaned_messages, 1):
            role = "MANAGER" if msg.get("role") == "manager" else "CLIENT"
            text = msg.get("text", "")
            dialog_lines.append(f"{i}. {role}: {text}")
        
        dialog_text = "\n".join(dialog_lines)
        
        # ПРОСТОЙ промпт (только ASCII)
        system_prompt = """You are a customer service supervisor. 
        Analyze this WhatsApp chat between manager and client.
        
        Give scores 1-10 for:
        1. Politeness
        2. Professionalism  
        3. Proactivity
        4. Response quality
        5. Communication effectiveness
        
        Return JSON ONLY:
        {
            "summary": "brief summary here",
            "scores": {
                "politeness": 0,
                "professionalism": 0,
                "proactivity": 0,
                "response_quality": 0,
                "effectiveness": 0
            },
            "total_score": 0,
            "key_errors": [],
            "improvement_suggestions": []
        }"""
        
        # API запрос
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": dialog_text}
            ],
            temperature=0.3,
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        
        # Парсим результат
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        # Очищаем результат
        cleaned_result = {}
        for key, value in result.items():
            if isinstance(value, str):
                cleaned_result[key] = clean_text(value)
            elif isinstance(value, dict):
                cleaned_dict = {}
                for k, v in value.items():
                    if isinstance(v, str):
                        cleaned_dict[clean_text(k)] = clean_text(v) if isinstance(v, str) else v
                    else:
                        cleaned_dict[clean_text(k)] = v
                cleaned_result[key] = cleaned_dict
            elif isinstance(value, list):
                cleaned_list = []
                for item in value:
                    if isinstance(item, str):
                        cleaned_list.append(clean_text(item))
                    else:
                        cleaned_list.append(item)
                cleaned_result[key] = cleaned_list
            else:
                cleaned_result[key] = value
        
        # Добавляем метаданные
        cleaned_result["analyzed_at"] = datetime.now().isoformat()
        cleaned_result["message_count"] = len(messages)
        cleaned_result["model_used"] = OPENAI_MODEL
        
        # Вычисляем общую оценку
        scores = cleaned_result.get("scores", {})
        total_score = 0
        if scores:
            for score in scores.values():
                if isinstance(score, (int, float)):
                    total_score += score
        
        cleaned_result["total_score"] = total_score
        
        # Определяем рейтинг
        if total_score >= 45:
            cleaned_result["verdict"] = "Excellent"
        elif total_score >= 35:
            cleaned_result["verdict"] = "Good"
        elif total_score >= 25:
            cleaned_result["verdict"] = "Satisfactory"
        else:
            cleaned_result["verdict"] = "Needs improvement"
        
        logger.info(f"Analysis successful! Score: {total_score}")
        return cleaned_result
        
    except json.JSONDecodeError as e:
        error_msg = f"JSON parsing error: {str(e)}"
        logger.error(error_msg)
        return create_error_response(error_msg)
    except openai.APIConnectionError as e:
        error_msg = f"OpenAI connection error: {str(e)}"
        logger.error(error_msg)
        return create_error_response(error_msg)
    except Exception as e:
        error_msg = f"Analysis error: {str(e)}"
        logger.error(error_msg)
        return create_error_response(error_msg)

def create_error_response(error_message: str) -> Dict[str, Any]:
    """Создает ответ об ошибке"""
    clean_error = clean_text(error_message)
    
    return {
        "error": True,
        "error_message": clean_error,
        "summary": f"Error: {clean_error[:50]}",
        "scores": {
            "politeness": 0,
            "professionalism": 0,
            "proactivity": 0,
            "response_quality": 0,
            "effectiveness": 0
        },
        "total_score": 0,
        "key_errors": [clean_error[:100]],
        "improvement_suggestions": ["Please try again"],
        "analyzed_at": datetime.now().isoformat()
    }

def format_chat_for_ai(messages: List[Dict[str, Any]]) -> str:
    """Форматирует диалог (для совместимости)"""
    return analyze_chat(messages)

def print_analysis_pretty(analysis: Dict[str, Any]):
    """Вывод результатов"""
    print("\n" + "="*60)
    print("ANALYSIS RESULTS")
    print("="*60)
    
    if analysis.get("error"):
        print(f"ERROR: {analysis.get('error_message', 'Unknown error')}")
        return
    
    print(f"SUMMARY: {analysis.get('summary', 'No summary')}")
    print(f"TOTAL SCORE: {analysis.get('total_score', 0)}/50")
    print(f"VERDICT: {analysis.get('verdict', '')}")
    
    if "scores" in analysis:
        print("\nSCORES:")
        for criterion, score in analysis["scores"].items():
            if isinstance(score, (int, float)):
                bar = "#" * int(score / 2) + "." * (5 - int(score / 2))
                print(f"  {criterion:20} {score:2}/10 {bar}")
    
    print("="*60)