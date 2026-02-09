from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta
import logging
import uuid
from typing import Dict, Any, List

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Папка для логов
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

# Глобальное хранилище (временное, позже заменим на БД)
chats_db: Dict[str, Dict] = {}
analyses_db: Dict[str, Dict] = {}
managers_db: Dict[str, Dict] = {
    "default": {"name": "Default Manager", "rating": 0, "total_chats": 0}
}

# Импортируем обработчики
from wazzup_handler import WazzupHandler, handle_wazzup_webhook
try:
    from analyzer_fixed import analyze_chat, print_analysis_pretty
    logger.info("✅ Using fixed analyzer")
except ImportError:
    from analyzer import analyze_chat, print_analysis_pretty
    logger.info("⚠️  Using original analyzer")

# Инициализируем Wazzup
try:
    wazzup = WazzupHandler()
    WAZZUP_ENABLED = True
    logger.info("✅ Wazzup handler initialized")
except Exception as e:
    WAZZUP_ENABLED = False
    logger.warning(f"❌ Wazzup disabled: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan контекст для startup/shutdown событий"""
    # Startup
    logger.info("🚀 Starting WABA AI Analyzer Server")
    
    # Проверяем конфигурацию
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("⚠️  OPENAI_API_KEY not set")
    
    if WAZZUP_ENABLED:
        logger.info("✅ Wazzup integration ready")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down server")
    # Сохраняем данные
    save_data_to_file()

def save_data_to_file():
    """Сохраняем данные в файл"""
    try:
        with open("data/chats_backup.json", "w") as f:
            json.dump(chats_db, f, default=str, indent=2)
        with open("data/analyses_backup.json", "w") as f:
            json.dump(analyses_db, f, default=str, indent=2)
        logger.info("💾 Data saved to files")
    except Exception as e:
        logger.error(f"❌ Error saving data: {e}")

def load_data_from_file():
    """Загружаем данные из файла"""
    global chats_db, analyses_db
    try:
        if os.path.exists("data/chats_backup.json"):
            with open("data/chats_backup.json", "r") as f:
                chats_db = json.load(f)
            logger.info(f"📂 Loaded {len(chats_db)} chats from backup")
        
        if os.path.exists("data/analyses_backup.json"):
            with open("data/analyses_backup.json", "r") as f:
                analyses_db = json.load(f)
            logger.info(f"📂 Loaded {len(analyses_db)} analyses from backup")
    except Exception as e:
        logger.error(f"❌ Error loading data: {e}")

# Загружаем данные при старте
load_data_from_file()

app = FastAPI(
    title="WABA AI Analyzer",
    version="1.0.0",
    description="AI-powered WhatsApp chat analyzer for quality control",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажи конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

def save_chat_to_db(chat_id: str, message_data: Dict[str, Any]):
    """Сохраняет сообщение в БД"""
    if chat_id not in chats_db:
        chats_db[chat_id] = {
            "id": chat_id,
            "client_number": message_data.get("client_number", chat_id),
            "manager_id": message_data.get("manager_id", "default"),
            "source": message_data.get("source", "wazzup"),
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "status": "active",
            "tags": []
        }
    
    # Добавляем сообщение
    message_entry = {
        "id": str(uuid.uuid4()),
        "role": message_data["role"],
        "text": message_data["text"],
        "timestamp": message_data.get("timestamp", datetime.now().isoformat()),
        "source": message_data.get("source", "wazzup"),
        "metadata": message_data.get("metadata", {})
    }
    
    chats_db[chat_id]["messages"].append(message_entry)
    chats_db[chat_id]["last_updated"] = datetime.now().isoformat()
    
    # Логируем
    with open(f"logs/chat_{chat_id}.json", "a") as f:
        f.write(json.dumps(message_entry, ensure_ascii=False, default=str) + "\n")
    
    logger.info(f"💾 Сообщение сохранено в чат {chat_id}")

@app.get("/")
async def root():
    """Главная страница API"""
    return {
        "status": "online",
        "service": "WABA AI Analyzer",
        "version": "1.0.0",
        "endpoints": {
            "webhook": "POST /webhook/wazzup",
            "chats": "GET /chats",
            "chat_detail": "GET /chats/{chat_id}",
            "analyze": "POST /analyze/{chat_id}",
            "analysis": "GET /analysis/{chat_id}",
            "dashboard": "GET /dashboard",
            "health": "GET /health",
            "send_test": "POST /send_test"
        },
        "integrations": {
            "wazzup": WAZZUP_ENABLED,
            "openai": bool(os.getenv("OPENAI_API_KEY"))
        },
        "stats": {
            "total_chats": len(chats_db),
            "total_analyses": len(analyses_db),
            "active_chats": len([c for c in chats_db.values() if c.get("status") == "active"])
        }
    }

@app.get("/health")
async def health():
    """Проверка работоспособности всех компонентов"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "api": "healthy",
            "database": "healthy" if chats_db is not None else "degraded",
            "openai": "configured" if os.getenv("OPENAI_API_KEY") else "not_configured",
            "wazzup": "enabled" if WAZZUP_ENABLED else "disabled"
        },
        "uptime": "0"  # Можно добавить расчет
    }
    
    # Проверяем OpenAI
    try:
        import openai
        if os.getenv("OPENAI_API_KEY"):
            health_status["components"]["openai"] = "healthy"
    except:
        health_status["components"]["openai"] = "error"
    
    return health_status

@app.post("/webhook/wazzup")
async def wazzup_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Вебхук Wazzup
    ⚠️ ВСЕГДА возвращаем 200 OK
    ⚙️ Вся логика уходит в background
    """
    try:
        data = await request.json()
        logger.info(f"📨 Wazzup webhook received: {json.dumps(data)[:300]}")

        # 👉 ВАЖНО: запускаем обработку в фоне
        background_tasks.add_task(process_wazzup_webhook, data)

    except Exception as e:
        logger.error(f"❌ Webhook parse error: {e}")

    # 🔥 ВСЕГДА 200 OK
    return JSONResponse({"status": "ok"})

async def process_wazzup_webhook(data: Dict[str, Any]):
    """Фоновая обработка вебхука Wazzup"""
    try:
        processed = handle_wazzup_webhook(data)
        
        if processed.get("chat_id"):
            # Сохраняем в нашу БД
            message_data = {
                "chat_id": processed["chat_id"],
                "role": processed["role"],
                "text": processed["text"],
                "timestamp": processed.get("timestamp", datetime.now().isoformat()),
                "source": "wazzup",
                "metadata": {
                    "message_id": processed.get("message_id"),
                    "sender": processed.get("sender", {})
                }
            }
            
            save_chat_to_db(processed["chat_id"], message_data)
            
            # Автоматически анализируем если диалог завершен
            if should_auto_analyze(processed["chat_id"]):
                logger.info(f"🤖 Авто-анализ диалога {processed['chat_id']}")
                try:
                    analysis = analyze_chat(chats_db[processed["chat_id"]]["messages"])
                    analyses_db[processed["chat_id"]] = {
                        **analysis,
                        "chat_id": processed["chat_id"],
                        "analyzed_at": datetime.now().isoformat(),
                        "auto_analyzed": True
                    }
                except Exception as e:
                    logger.error(f"❌ Auto-analysis failed: {e}")
    
    except Exception as e:
        logger.error(f"❌ Background processing error: {e}")

def should_auto_analyze(chat_id: str) -> bool:
    """Определяет, нужно ли автоматически анализировать диалог"""
    if chat_id not in chats_db:
        return False
    
    messages = chats_db[chat_id]["messages"]
    if len(messages) < 3:
        return False
    
    # Анализируем если есть хотя бы 2 сообщения менеджера и диалог не анализировался сегодня
    manager_msgs = [m for m in messages if m["role"] == "manager"]
    
    if len(manager_msgs) >= 2:
        # Проверяем, не анализировался ли сегодня
        if chat_id in analyses_db:
            last_analysis = analyses_db[chat_id].get("analyzed_at", "")
            if last_analysis:
                try:
                    last_date = datetime.fromisoformat(last_analysis.replace('Z', '+00:00'))
                    if (datetime.now() - last_date) < timedelta(hours=1):
                        return False
                except:
                    pass
        
        return True
    
    return False

@app.get("/chats")
async def get_chats(
    limit: int = 50,
    offset: int = 0,
    status: str = None,
    manager_id: str = None
):
    """Получить список диалогов с фильтрацией"""
    filtered_chats = list(chats_db.values())
    
    # Фильтрация
    if status:
        filtered_chats = [c for c in filtered_chats if c.get("status") == status]
    
    if manager_id:
        filtered_chats = [c for c in filtered_chats if c.get("manager_id") == manager_id]
    
    # Сортировка по времени
    filtered_chats.sort(key=lambda x: x.get("last_updated", ""), reverse=True)
    
    # Пагинация
    paginated = filtered_chats[offset:offset + limit]
    
    # Форматируем ответ
    formatted_chats = []
    for chat in paginated:
        messages = chat.get("messages", [])
        manager_msgs = [m for m in messages if m["role"] == "manager"]
        client_msgs = [m for m in messages if m["role"] == "client"]
        
        formatted_chats.append({
            "id": chat["id"],
            "client_number": chat.get("client_number", "unknown"),
            "manager_id": chat.get("manager_id", "default"),
            "message_count": len(messages),
            "manager_message_count": len(manager_msgs),
            "client_message_count": len(client_msgs),
            "created_at": chat.get("created_at"),
            "last_updated": chat.get("last_updated"),
            "last_message": messages[-1]["text"][:100] if messages else "",
            "status": chat.get("status", "active"),
            "has_analysis": chat["id"] in analyses_db
        })
    
    return {
        "chats": formatted_chats,
        "total": len(filtered_chats),
        "limit": limit,
        "offset": offset
    }

@app.get("/chats/{chat_id}")
async def get_chat(chat_id: str):
    """Получить конкретный диалог"""
    if chat_id not in chats_db:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    chat = chats_db[chat_id]
    
    # Форматируем сообщения для удобства
    formatted_messages = []
    for msg in chat.get("messages", []):
        formatted_messages.append({
            "id": msg["id"],
            "role": msg["role"],
            "text": msg["text"],
            "time": msg.get("timestamp"),
            "short_text": msg["text"][:150] + ("..." if len(msg["text"]) > 150 else "")
        })
    
    return {
        "chat": chat,
        "messages": formatted_messages,
        "analysis_available": chat_id in analyses_db
    }

@app.post("/analyze/{chat_id}")
async def analyze_chat_endpoint(
    chat_id: str,
    force: bool = False,
    background: bool = False
):
    """Запустить анализ диалога через ИИ"""
    if chat_id not in chats_db:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    chat = chats_db[chat_id]
    messages = chat.get("messages", [])
    
    if len(messages) < 2:
        return {"error": "Диалог слишком короткий для анализа", "min_messages": 2}
    
    # Проверяем, не анализировался ли недавно
    if not force and chat_id in analyses_db:
        last_analysis = analyses_db[chat_id].get("analyzed_at", "")
        if last_analysis:
            try:
                last_date = datetime.fromisoformat(last_analysis.replace('Z', '+00:00'))
                if (datetime.now() - last_date) < timedelta(minutes=5):
                    return {
                        "warning": "Диалог недавно анализировался",
                        "last_analysis": last_analysis,
                        "use_force": True
                    }
            except:
                pass
    
    if background:
        # Фоновый анализ
        from analyzer import analyze_chat_async
        import asyncio
        
        task_id = str(uuid.uuid4())
        asyncio.create_task(
            analyze_chat_async(chat_id, messages, task_id)
        )
        
        return {
            "status": "analysis_started",
            "task_id": task_id,
            "chat_id": chat_id,
            "message": "Анализ запущен в фоновом режиме"
        }
    else:
        # Синхронный анализ
        try:
            logger.info(f"🤖 Начинаю анализ диалога {chat_id} ({len(messages)} сообщений)")
            
            analysis_result = analyze_chat(messages)
            
            # Сохраняем результат
            analyses_db[chat_id] = {
                **analysis_result,
                "chat_id": chat_id,
                "analyzed_at": datetime.now().isoformat(),
                "message_count": len(messages),
                "auto_analyzed": False
            }
            
            # Логируем
            with open(f"logs/analysis_{chat_id}.json", "w") as f:
                json.dump(analyses_db[chat_id], f, ensure_ascii=False, indent=2, default=str)
            
            # Обновляем статистику менеджера
            manager_id = chat.get("manager_id", "default")
            if manager_id not in managers_db:
                managers_db[manager_id] = {"name": manager_id, "rating": 0, "total_chats": 0}
            
            managers_db[manager_id]["total_chats"] += 1
            if "total_score" in analysis_result:
                managers_db[manager_id]["rating"] = (
                    managers_db[manager_id].get("rating", 0) + analysis_result["total_score"]
                ) / 2
            
            logger.info(f"✅ Анализ завершен. Оценка: {analysis_result.get('total_score', 0)}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа: {e}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/analysis/{chat_id}")
async def get_analysis(chat_id: str, pretty: bool = False):
    """Получить результат анализа"""
    if chat_id not in analyses_db:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analyses_db[chat_id]
    
    if pretty:
        # Форматируем для удобного чтения
        formatted = {
            "summary": analysis.get("summary", "Нет данных"),
            "total_score": analysis.get("total_score", 0),
            "scores": analysis.get("scores", {}),
            "key_errors": analysis.get("key_errors", []),
            "improvement_suggestions": analysis.get("improvement_suggestions", []),
            "analyzed_at": analysis.get("analyzed_at"),
            "message_count": analysis.get("message_count", 0)
        }
        return formatted
    
    return analysis

@app.get("/dashboard")
async def get_dashboard():
    """Дашборд со статистикой"""
    total_chats = len(chats_db)
    total_analyses = len(analyses_db)
    
    # Считаем сообщения
    total_messages = 0
    for chat in chats_db.values():
        total_messages += len(chat.get("messages", []))
    
    # Средняя оценка
    avg_score = 0
    if analyses_db:
        scores = [a.get("total_score", 0) for a in analyses_db.values() if a.get("total_score")]
        avg_score = sum(scores) / len(scores) if scores else 0
    
    # Активные чаты (последние 24 часа)
    active_chats = 0
    day_ago = datetime.now() - timedelta(hours=24)
    for chat in chats_db.values():
        last_updated = chat.get("last_updated")
        if last_updated:
            try:
                last_date = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                if last_date > day_ago:
                    active_chats += 1
            except:
                pass
    
    # Топ ошибок
    common_errors = {}
    for analysis in analyses_db.values():
        errors = analysis.get("key_errors", [])
        for error in errors:
            common_errors[error] = common_errors.get(error, 0) + 1
    
    top_errors = sorted(common_errors.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "overview": {
            "total_chats": total_chats,
            "active_chats": active_chats,
            "total_messages": total_messages,
            "total_analyses": total_analyses,
            "average_score": round(avg_score, 1),
            "uptime": "0"  # Можно добавить
        },
        "managers": [
            {
                "id": mid,
                **data,
                "chat_count": len([c for c in chats_db.values() if c.get("manager_id") == mid])
            }
            for mid, data in managers_db.items()
        ],
        "recent_analyses": [
            {
                "chat_id": chat_id,
                "score": analyses_db[chat_id].get("total_score", 0),
                "analyzed_at": analyses_db[chat_id].get("analyzed_at"),
                "summary": analyses_db[chat_id].get("summary", "")[:100]
            }
            for chat_id in list(analyses_db.keys())[:5]
        ],
        "common_errors": [
            {"error": error, "count": count} for error, count in top_errors
        ]
    }

@app.post("/send_test")
async def send_test_message(
    phone: str,
    message: str = "🤖 Тестовое сообщение от AI-анализатора"
):
    """Отправить тестовое сообщение через Wazzup (для тестирования)"""
    if not WAZZUP_ENABLED:
        raise HTTPException(status_code=501, detail="Wazzup not configured")
    
    try:
        result = wazzup.send_message(phone, message)
        
        # Сохраняем отправленное сообщение
        test_chat_id = f"test_{phone}"
        message_data = {
            "chat_id": test_chat_id,
            "role": "manager",
            "text": message,
            "timestamp": datetime.now().isoformat(),
            "source": "test",
            "metadata": {"test": True, "result": result}
        }
        
        save_chat_to_db(test_chat_id, message_data)
        
        return {
            "status": "sent",
            "chat_id": test_chat_id,
            "result": result,
            "message": f"Тестовое сообщение отправлено на {phone}"
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки тестового сообщения: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/chat/{chat_id}/raw")
async def debug_chat_raw(chat_id: str):
    """Отладка: сырые данные чата"""
    if chat_id not in chats_db:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return chats_db[chat_id]

@app.get("/debug/analysis/{chat_id}/raw")
async def debug_analysis_raw(chat_id: str):
    """Отладка: сырые данные анализа"""
    if chat_id not in analyses_db:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analyses_db[chat_id]

# Запуск сервера
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=True,
        log_config=None,
        access_log=True
    )