# from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Depends
# from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# from contextlib import asynccontextmanager
# from dotenv import load_dotenv
# import os
# import json
# import csv
# import io
# from datetime import datetime, timedelta
# import logging
# import uuid
# from typing import Dict, Any, List, Optional

# # Загружаем переменные окружения
# load_dotenv()

# # Настройка логирования
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# # Папка для логов
# os.makedirs("logs", exist_ok=True)
# os.makedirs("data", exist_ok=True)

# # Глобальное хранилище
# chats_db: Dict[str, Dict] = {}
# analyses_pro_db: Dict[str, Dict] = {}  # Для профессиональных анализов
# managers_db: Dict[str, Dict] = {
#     "default": {"name": "Default Manager", "rating": 0, "total_chats": 0}
# }

# # Импортируем профессиональный анализатор
# try:
#     from analyzer_pro import analyze_chat_pro, convert_to_table_row, get_table_headers, export_to_csv
#     logger.info("✅ Professional analyzer loaded")
# except ImportError as e:
#     logger.error(f"❌ Failed to load professional analyzer: {e}")
#     analyze_chat_pro = None

# # Импортируем обработчики
# from wazzup_handler import WazzupHandler, handle_wazzup_webhook

# # Инициализируем Wazzup
# try:
#     wazzup = WazzupHandler()
#     WAZZUP_ENABLED = True
#     logger.info("✅ Wazzup handler initialized")
# except Exception as e:
#     WAZZUP_ENABLED = False
#     logger.warning(f"❌ Wazzup disabled: {e}")

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Lifespan контекст для startup/shutdown событий"""
#     # Startup
#     logger.info("🚀 Starting WABA AI Professional Analyzer Server")
    
#     # Проверяем конфигурацию
#     if not os.getenv("OPENAI_API_KEY"):
#         logger.warning("⚠️  OPENAI_API_KEY not set")
    
#     if WAZZUP_ENABLED:
#         logger.info("✅ Wazzup integration ready")
    
#     if analyze_chat_pro:
#         logger.info("✅ Professional analyzer ready")
#     else:
#         logger.error("❌ Professional analyzer not available")
    
#     yield
    
#     # Shutdown
#     logger.info("👋 Shutting down server")
#     save_data_to_file()

# def save_data_to_file():
#     """Сохраняем данные в файл"""
#     try:
#         with open("data/chats_backup.json", "w") as f:
#             json.dump(chats_db, f, default=str, indent=2)
#         with open("data/analyses_pro_backup.json", "w") as f:
#             json.dump(analyses_pro_db, f, default=str, indent=2)
#         logger.info("💾 Data saved to files")
#     except Exception as e:
#         logger.error(f"❌ Error saving data: {e}")

# def load_data_from_file():
#     """Загружаем данные из файла"""
#     global chats_db, analyses_pro_db
#     try:
#         if os.path.exists("data/chats_backup.json"):
#             with open("data/chats_backup.json", "r") as f:
#                 chats_db = json.load(f)
#             logger.info(f"📂 Loaded {len(chats_db)} chats from backup")
        
#         if os.path.exists("data/analyses_pro_backup.json"):
#             with open("data/analyses_pro_backup.json", "r") as f:
#                 analyses_pro_db = json.load(f)
#             logger.info(f"📂 Loaded {len(analyses_pro_db)} professional analyses from backup")
#     except Exception as e:
#         logger.error(f"❌ Error loading data: {e}")

# # Загружаем данные при старте
# load_data_from_file()

# app = FastAPI(
#     title="WABA AI Professional Analyzer",
#     version="2.0.0",
#     description="Professional AI-powered chat analyzer for quality control with OKC methodology",
#     lifespan=lifespan
# )

# # CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Mount static files
# app.mount("/static", StaticFiles(directory="static"), name="static")

# def save_chat_to_db(chat_id: str, message_data: Dict[str, Any]):
#     """Сохраняет сообщение в БД"""
#     if chat_id not in chats_db:
#         chats_db[chat_id] = {
#             "id": chat_id,
#             "client_number": message_data.get("client_number", chat_id),
#             "manager_id": message_data.get("manager_id", "default"),
#             "source": message_data.get("source", "wazzup"),
#             "messages": [],
#             "created_at": datetime.now().isoformat(),
#             "last_updated": datetime.now().isoformat(),
#             "status": "active",
#             "tags": [],
#             "metadata": {
#                 "manager_name": message_data.get("manager_name", "Unknown"),
#                 "channel": message_data.get("channel", "whatsapp"),
#                 "funnel_stage": message_data.get("funnel_stage", "unknown")
#             }
#         }
    
#     # Добавляем сообщение
#     message_entry = {
#         "id": str(uuid.uuid4()),
#         "role": message_data["role"],
#         "text": message_data["text"],
#         "timestamp": message_data.get("timestamp", datetime.now().isoformat()),
#         "source": message_data.get("source", "wazzup"),
#         "metadata": message_data.get("metadata", {})
#     }
    
#     chats_db[chat_id]["messages"].append(message_entry)
#     chats_db[chat_id]["last_updated"] = datetime.now().isoformat()
    
#     logger.info(f"💾 Сообщение сохранено в чат {chat_id}")

# @app.get("/")
# async def root():
#     """Главная страница API"""
#     return {
#         "status": "online",
#         "service": "WABA AI Professional Analyzer",
#         "version": "2.0.0",
#         "methodology": "ОКК (Отдел Контроля Качества Коммуникаций)",
#         "endpoints": {
#             "webhook": "POST /webhook/wazzup",
#             "chats": "GET /chats",
#             "chat_detail": "GET /chats/{chat_id}",
#             "analyze_pro": "POST /analyze/pro/{chat_id}",
#             "analyze_batch_pro": "POST /analyze/pro/batch",
#             "get_analysis_pro": "GET /analysis/pro/{chat_id}",
#             "export_csv": "GET /export/csv",
#             "dashboard_pro": "GET /dashboard/pro",
#             "health": "GET /health"
#         },
#         "integrations": {
#             "wazzup": WAZZUP_ENABLED,
#             "openai": bool(os.getenv("OPENAI_API_KEY")),
#             "professional_analyzer": analyze_chat_pro is not None
#         },
#         "stats": {
#             "total_chats": len(chats_db),
#             "total_pro_analyses": len(analyses_pro_db),
#             "active_chats": len([c for c in chats_db.values() if c.get("status") == "active"])
#         }
#     }

# @app.get("/health")
# async def health():
#     """Проверка работоспособности"""
#     return {
#         "status": "healthy",
#         "timestamp": datetime.now().isoformat(),
#         "components": {
#             "api": "healthy",
#             "database": "healthy",
#             "openai": "configured" if os.getenv("OPENAI_API_KEY") else "not_configured",
#             "wazzup": "enabled" if WAZZUP_ENABLED else "disabled",
#             "professional_analyzer": "ready" if analyze_chat_pro else "not_available"
#         }
#     }

# @app.post("/webhook/wazzup")
# async def wazzup_webhook(request: Request, background_tasks: BackgroundTasks):
#     """
#     Вебхук Wazzup
#     """
#     try:
#         data = await request.json()
#         logger.info(f"📨 Wazzup webhook received")

#         # Фоновая обработка
#         background_tasks.add_task(process_wazzup_webhook, data)

#     except Exception as e:
#         logger.error(f"❌ Webhook parse error: {e}")

#     return JSONResponse({"status": "ok"})

# async def process_wazzup_webhook(data: Dict[str, Any]):
#     """Фоновая обработка вебхука Wazzup"""
#     try:
#         processed = handle_wazzup_webhook(data)
        
#         if processed.get("chat_id"):
#             # Сохраняем в нашу БД
#             message_data = {
#                 "chat_id": processed["chat_id"],
#                 "role": processed["role"],
#                 "text": processed["text"],
#                 "timestamp": processed.get("timestamp", datetime.now().isoformat()),
#                 "source": "wazzup",
#                 "metadata": {
#                     "message_id": processed.get("message_id"),
#                     "sender": processed.get("sender", {})
#                 }
#             }
            
#             save_chat_to_db(processed["chat_id"], message_data)
    
#     except Exception as e:
#         logger.error(f"❌ Background processing error: {e}")

# @app.get("/chats")
# async def get_chats(
#     limit: int = 50,
#     offset: int = 0,
#     status: str = None,
#     manager_id: str = None,
#     with_analysis: bool = False
# ):
#     """Получить список диалогов"""
#     filtered_chats = list(chats_db.values())
    
#     # Фильтрация
#     if status:
#         filtered_chats = [c for c in filtered_chats if c.get("status") == status]
    
#     if manager_id:
#         filtered_chats = [c for c in filtered_chats if c.get("manager_id") == manager_id]
    
#     # Сортировка
#     filtered_chats.sort(key=lambda x: x.get("last_updated", ""), reverse=True)
    
#     # Пагинация
#     paginated = filtered_chats[offset:offset + limit]
    
#     # Форматируем ответ
#     formatted_chats = []
#     for chat in paginated:
#         chat_id = chat["id"]
#         messages = chat.get("messages", [])
        
#         formatted_chats.append({
#             "id": chat_id,
#             "client_number": chat.get("client_number", "unknown"),
#             "manager_id": chat.get("manager_id", "default"),
#             "manager_name": chat.get("metadata", {}).get("manager_name", "Unknown"),
#             "message_count": len(messages),
#             "created_at": chat.get("created_at"),
#             "last_updated": chat.get("last_updated"),
#             "status": chat.get("status", "active"),
#             "has_pro_analysis": chat_id in analyses_pro_db,
#             "pro_score": analyses_pro_db.get(chat_id, {}).get("summary_score", 0) if chat_id in analyses_pro_db else None,
#             "last_message": messages[-1]["text"][:100] if messages else ""
#         })
    
#     return {
#         "chats": formatted_chats,
#         "total": len(filtered_chats),
#         "limit": limit,
#         "offset": offset
#     }

# @app.get("/chats/{chat_id}")
# async def get_chat(chat_id: str):
#     """Получить конкретный диалог"""
#     if chat_id not in chats_db:
#         raise HTTPException(status_code=404, detail="Chat not found")
    
#     chat = chats_db[chat_id]
    
#     # Форматируем сообщения
#     formatted_messages = []
#     for msg in chat.get("messages", []):
#         formatted_messages.append({
#             "id": msg["id"],
#             "role": msg["role"],
#             "text": msg["text"],
#             "time": msg.get("timestamp"),
#             "short_text": msg["text"][:150] + ("..." if len(msg["text"]) > 150 else "")
#         })
    
#     return {
#         "chat": chat,
#         "messages": formatted_messages,
#         "pro_analysis_available": chat_id in analyses_pro_db
#     }

# @app.post("/analyze/pro/{chat_id}")
# async def analyze_chat_pro_endpoint(
#     chat_id: str,
#     force: bool = False
# ):
#     """Профессиональный анализ диалога по методологии ОКК"""
#     if not analyze_chat_pro:
#         raise HTTPException(status_code=501, detail="Professional analyzer not available")
    
#     if chat_id not in chats_db:
#         raise HTTPException(status_code=404, detail="Chat not found")
    
#     chat = chats_db[chat_id]
#     messages = chat.get("messages", [])
    
#     if len(messages) < 2:
#         return {"error": "Диалог слишком короткий для анализа", "min_messages": 2}
    
#     # Проверяем, не анализировался ли недавно
#     if not force and chat_id in analyses_pro_db:
#         last_analysis = analyses_pro_db[chat_id].get("analysis_timestamp", "")
#         if last_analysis:
#             try:
#                 last_date = datetime.fromisoformat(last_analysis.replace('Z', '+00:00'))
#                 if (datetime.now() - last_date) < timedelta(minutes=10):
#                     return {
#                         "warning": "Диалог недавно анализировался",
#                         "last_analysis": last_analysis,
#                         "use_force": True
#                     }
#             except:
#                 pass
    
#     try:
#         logger.info(f"🔍 Запускаю профессиональный анализ диалога {chat_id}")
        
#         # Подготавливаем метаданные
#         metadata = {
#             "manager": chat.get("metadata", {}).get("manager_name", chat.get("manager_id", "default")),
#             "channel": chat.get("metadata", {}).get("channel", "whatsapp"),
#             "datetime": chat.get("created_at", ""),
#             "funnel_stage": chat.get("metadata", {}).get("funnel_stage", "unknown"),
#             "crm_link": f"chat_{chat_id}",
#             "chat_id": chat_id
#         }
        
#         # Запускаем профессиональный анализ
#         analysis_result = analyze_chat_pro(messages, metadata)
        
#         # Сохраняем результат
#         analyses_pro_db[chat_id] = analysis_result
        
#         # Обновляем статистику менеджера
#         manager_id = chat.get("manager_id", "default")
#         if manager_id not in managers_db:
#             managers_db[manager_id] = {"name": manager_id, "rating": 0, "total_chats": 0}
        
#         managers_db[manager_id]["total_chats"] += 1
#         if "summary_score" in analysis_result:
#             # Обновляем рейтинг менеджера
#             current_rating = managers_db[manager_id].get("rating", 0)
#             new_score = analysis_result["summary_score"]
#             managers_db[manager_id]["rating"] = (current_rating + new_score) / 2
        
#         logger.info(f"✅ Профессиональный анализ завершен. Счет: {analysis_result.get('summary_score', 0)}/100")
        
#         # Возвращаем также табличную строку
#         table_row = convert_to_table_row(analysis_result, chat_id)
        
#         return {
#             "status": "success",
#             "analysis": analysis_result,
#             "table_row": table_row,
#             "chat_id": chat_id,
#             "score": analysis_result.get("summary_score", 0)
#         }
        
#     except Exception as e:
#         logger.error(f"❌ Ошибка профессионального анализа: {e}")
#         raise HTTPException(status_code=500, detail=f"Professional analysis failed: {str(e)}")

# @app.get("/analysis/pro/{chat_id}")
# async def get_pro_analysis(chat_id: str, format: str = "json"):
#     """Получить результат профессионального анализа"""
#     if chat_id not in analyses_pro_db:
#         raise HTTPException(status_code=404, detail="Professional analysis not found")
    
#     analysis = analyses_pro_db[chat_id]
    
#     if format == "table":
#         # Возвращаем табличную строку
#         return convert_to_table_row(analysis, chat_id)
#     elif format == "csv":
#         # Возвращаем как CSV строку
#         row = convert_to_table_row(analysis, chat_id)
#         headers = get_table_headers()
        
#         output = io.StringIO()
#         writer = csv.DictWriter(output, fieldnames=headers, delimiter=';')
#         writer.writeheader()
#         writer.writerow(row)
        
#         return StreamingResponse(
#             iter([output.getvalue()]),
#             media_type="text/csv",
#             headers={"Content-Disposition": f"attachment; filename=analysis_{chat_id}.csv"}
#         )
#     else:
#         # Возвращаем полный JSON
#         return analysis

# @app.post("/analyze/pro/batch")
# async def analyze_batch_pro(
#     start_date: str = None,
#     end_date: str = None,
#     manager_id: str = None,
#     min_messages: int = 3,
#     limit: int = 10,
#     force: bool = False
# ):
#     """
#     Массовый профессиональный анализ диалогов
#     """
#     if not analyze_chat_pro:
#         raise HTTPException(status_code=501, detail="Professional analyzer not available")
    
#     try:
#         filtered_chats = []
        
#         for chat_id, chat in chats_db.items():
#             # Фильтрация по дате
#             if start_date:
#                 chat_date = datetime.fromisoformat(chat.get("created_at", "2000-01-01").replace('Z', '+00:00'))
#                 start_datetime = datetime.fromisoformat(start_date)
#                 if chat_date < start_datetime:
#                     continue
            
#             if end_date:
#                 chat_date = datetime.fromisoformat(chat.get("created_at", "2000-01-01").replace('Z', '+00:00'))
#                 end_datetime = datetime.fromisoformat(end_date)
#                 if chat_date > end_datetime:
#                     continue
            
#             # Фильтрация по менеджеру
#             if manager_id and chat.get("manager_id") != manager_id:
#                 continue
            
#             # Фильтрация по количеству сообщений
#             if len(chat.get("messages", [])) < min_messages:
#                 continue
            
#             # Проверяем, не анализировался ли недавно
#             if not force and chat_id in analyses_pro_db:
#                 last_analysis = analyses_pro_db[chat_id].get("analysis_timestamp", "")
#                 if last_analysis:
#                     try:
#                         last_date = datetime.fromisoformat(last_analysis.replace('Z', '+00:00'))
#                         if (datetime.now() - last_date) < timedelta(hours=12):
#                             continue
#                     except:
#                         pass
            
#             filtered_chats.append((chat_id, chat))
        
#         # Ограничиваем количество
#         filtered_chats = filtered_chats[:limit]
        
#         if not filtered_chats:
#             return {
#                 "message": "Нет диалогов по заданным критериям",
#                 "filters": {
#                     "start_date": start_date,
#                     "end_date": end_date,
#                     "manager_id": manager_id,
#                     "min_messages": min_messages,
#                     "limit": limit
#                 },
#                 "total_chats": len(chats_db)
#             }
        
#         results = []
#         table_rows = []
        
#         # Синхронный анализ (может быть долго!)
#         for chat_id, chat in filtered_chats:
#             try:
#                 # Подготавливаем метаданные
#                 metadata = {
#                     "manager": chat.get("metadata", {}).get("manager_name", chat.get("manager_id", "default")),
#                     "channel": chat.get("metadata", {}).get("channel", "whatsapp"),
#                     "datetime": chat.get("created_at", ""),
#                     "funnel_stage": chat.get("metadata", {}).get("funnel_stage", "unknown"),
#                     "crm_link": f"chat_{chat_id}",
#                     "chat_id": chat_id
#                 }
                
#                 analysis_result = analyze_chat_pro(chat["messages"], metadata)
                
#                 # Сохраняем результат
#                 analyses_pro_db[chat_id] = analysis_result
                
#                 # Табличная строка
#                 table_row = convert_to_table_row(analysis_result, chat_id)
#                 table_rows.append(table_row)
                
#                 results.append({
#                     "chat_id": chat_id,
#                     "success": True,
#                     "score": analysis_result.get("summary_score", 0),
#                     "client": chat.get("client_number", "unknown"),
#                     "manager": chat.get("manager_id", "default")
#                 })
                
#                 # Небольшая пауза чтобы не перегружать API
#                 import time
#                 time.sleep(0.5)
                
#             except Exception as e:
#                 results.append({
#                     "chat_id": chat_id,
#                     "success": False,
#                     "error": str(e)[:100]
#                 })
        
#         # Считаем статистику
#         successful = [r for r in results if r["success"]]
#         avg_score = sum(r["score"] for r in successful) / len(successful) if successful else 0
        
#         return {
#             "batch_completed": True,
#             "total_analyzed": len(filtered_chats),
#             "successful": len(successful),
#             "failed": len(results) - len(successful),
#             "average_score": round(avg_score, 1),
#             "results": results,
#             "table_rows": table_rows
#         }
    
#     except Exception as e:
#         logger.error(f"❌ Batch professional analysis error: {e}")
#         raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

# @app.get("/export/csv")
# async def export_analyses_csv(
#     start_date: str = None,
#     end_date: str = None,
#     manager_id: str = None
# ):
#     """Экспорт всех анализов в CSV"""
    
#     # Фильтруем анализы
#     filtered_analyses = []
#     for chat_id, analysis in analyses_pro_db.items():
#         # Пропускаем ошибки
#         if analysis.get("error"):
#             continue
        
#         # Фильтрация по дате анализа
#         if start_date:
#             analysis_date = datetime.fromisoformat(analysis.get("analysis_timestamp", "2000-01-01").replace('Z', '+00:00'))
#             start_datetime = datetime.fromisoformat(start_date)
#             if analysis_date < start_datetime:
#                 continue
        
#         if end_date:
#             analysis_date = datetime.fromisoformat(analysis.get("analysis_timestamp", "2000-01-01").replace('Z', '+00:00'))
#             end_datetime = datetime.fromisoformat(end_date)
#             if analysis_date > end_datetime:
#                 continue
        
#         # Фильтрация по менеджеру
#         if manager_id:
#             analysis_manager = analysis.get("l0_context", {}).get("manager", "")
#             if str(analysis_manager) != str(manager_id):
#                 continue
        
#         filtered_analyses.append(analysis)
    
#     if not filtered_analyses:
#         raise HTTPException(status_code=404, detail="No analyses found for export")
    
#     # Конвертируем в табличные строки
#     table_rows = []
#     for analysis in filtered_analyses:
#         chat_id = analysis.get("chat_id", "unknown")
#         table_row = convert_to_table_row(analysis, chat_id)
#         table_rows.append(table_row)
    
#     # Создаем CSV в памяти
#     output = io.StringIO()
#     headers = get_table_headers()
    
#     writer = csv.DictWriter(output, fieldnames=headers, delimiter=';')
#     writer.writeheader()
#     writer.writerows(table_rows)
    
#     # Генерируем имя файла
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     filename = f"okc_analytics_export_{timestamp}.csv"
    
#     return StreamingResponse(
#         iter([output.getvalue()]),
#         media_type="text/csv",
#         headers={"Content-Disposition": f"attachment; filename={filename}"}
#     )

# @app.get("/dashboard/pro")
# async def get_dashboard_pro():
#     """Дашборд профессиональной аналитики"""
    
#     total_chats = len(chats_db)
#     total_analyses = len(analyses_pro_db)
    
#     # Собираем статистику по анализам
#     scores = []
#     managers_stats = {}
#     channel_stats = {}
#     funnel_stats = {}
    
#     for chat_id, analysis in analyses_pro_db.items():
#         if analysis.get("error"):
#             continue
        
#         score = analysis.get("summary_score", 0)
#         scores.append(score)
        
#         # Статистика по менеджерам
#         manager = analysis.get("l0_context", {}).get("manager", "unknown")
#         if manager not in managers_stats:
#             managers_stats[manager] = {"count": 0, "total_score": 0, "chats": []}
        
#         managers_stats[manager]["count"] += 1
#         managers_stats[manager]["total_score"] += score
#         managers_stats[manager]["chats"].append(chat_id)
        
#         # Статистика по каналам
#         channel = analysis.get("l0_context", {}).get("channel", "unknown")
#         if channel not in channel_stats:
#             channel_stats[channel] = {"count": 0, "total_score": 0}
        
#         channel_stats[channel]["count"] += 1
#         channel_stats[channel]["total_score"] += score
        
#         # Статистика по этапам воронки
#         funnel = analysis.get("l0_context", {}).get("funnel_stage", "unknown")
#         if funnel not in funnel_stats:
#             funnel_stats[funnel] = {"count": 0, "total_score": 0}
        
#         funnel_stats[funnel]["count"] += 1
#         funnel_stats[funnel]["total_score"] += score
    
#     # Рассчитываем средние
#     avg_score = sum(scores) / len(scores) if scores else 0
    
#     # Топ менеджеров
#     top_managers = []
#     for manager, stats in managers_stats.items():
#         avg_manager_score = stats["total_score"] / stats["count"] if stats["count"] > 0 else 0
#         top_managers.append({
#             "manager": manager,
#             "chat_count": stats["count"],
#             "average_score": round(avg_manager_score, 1),
#             "chat_ids": stats["chats"][:5]  # Первые 5 чатов
#         })
    
#     # Сортируем по среднему счету
#     top_managers.sort(key=lambda x: x["average_score"], reverse=True)
    
#     # Распределение по оценкам
#     score_distribution = {
#         "excellent": len([s for s in scores if s >= 80]),
#         "good": len([s for s in scores if 60 <= s < 80]),
#         "average": len([s for s in scores if 40 <= s < 60]),
#         "poor": len([s for s in scores if s < 40])
#     }
    
#     # Топ проблем (из missed_opportunities)
#     common_problems = {}
#     for analysis in analyses_pro_db.values():
#         if analysis.get("error"):
#             continue
        
#         missed = analysis.get("l6_recommendations", {}).get("missed_opportunities", [])
#         for problem in missed:
#             if problem not in common_problems:
#                 common_problems[problem] = 0
#             common_problems[problem] += 1
    
#     top_problems = sorted(common_problems.items(), key=lambda x: x[1], reverse=True)[:5]
    
#     # Последние анализы
#     recent_analyses = []
#     for chat_id in list(analyses_pro_db.keys())[-5:]:  # Последние 5
#         analysis = analyses_pro_db[chat_id]
#         if not analysis.get("error"):
#             recent_analyses.append({
#                 "chat_id": chat_id,
#                 "score": analysis.get("summary_score", 0),
#                 "manager": analysis.get("l0_context", {}).get("manager", "unknown"),
#                 "analyzed_at": analysis.get("analysis_timestamp", ""),
#                 "final_status": analysis.get("l5_dialog_result", {}).get("final_status", "unknown")
#             })
    
#     return {
#         "overview": {
#             "total_chats": total_chats,
#             "total_analyses": total_analyses,
#             "coverage_percentage": round((total_analyses / total_chats * 100), 1) if total_chats > 0 else 0,
#             "average_score": round(avg_score, 1),
#             "analysis_timestamp": datetime.now().isoformat()
#         },
#         "score_distribution": score_distribution,
#         "top_managers": top_managers[:5],  # Топ 5
#         "channel_performance": [
#             {
#                 "channel": channel,
#                 "count": stats["count"],
#                 "average_score": round(stats["total_score"] / stats["count"], 1) if stats["count"] > 0 else 0
#             }
#             for channel, stats in channel_stats.items()
#         ],
#         "funnel_performance": [
#             {
#                 "stage": stage,
#                 "count": stats["count"],
#                 "average_score": round(stats["total_score"] / stats["count"], 1) if stats["count"] > 0 else 0
#             }
#             for stage, stats in funnel_stats.items()
#         ],
#         "common_problems": [{"problem": p[0], "count": p[1]} for p in top_problems],
#         "recent_analyses": recent_analyses
#     }

# @app.get("/debug/pro/table/{chat_id}")
# async def debug_pro_table(chat_id: str):
#     """Отладка: табличная строка анализа"""
#     if chat_id not in analyses_pro_db:
#         raise HTTPException(status_code=404, detail="Analysis not found")
    
#     analysis = analyses_pro_db[chat_id]
#     table_row = convert_to_table_row(analysis, chat_id)
    
#     # Красивый вывод в виде таблицы
#     import pandas as pd
    
#     df = pd.DataFrame([table_row])
    
#     return {
#         "chat_id": chat_id,
#         "table_row": table_row,
#         "html_table": df.to_html(index=False),
#         "markdown_table": df.to_markdown(index=False)
#     }

# # Запуск сервера
# if __name__ == "__main__":
#     import uvicorn
    
#     port = int(os.getenv("PORT", 8000))
    
#     uvicorn.run(
#         "main_pro:app",
#         host="0.0.0.0",
#         port=port,
#         reload=True,
#         log_level="info"
#     )





from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
import json
import csv
import io
from datetime import datetime, timedelta
import logging
import uuid
from typing import Dict, Any, List, Optional

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

# Глобальное хранилище
chats_db: Dict[str, Dict] = {}
analyses_pro_db: Dict[str, Dict] = {}  # Для профессиональных анализов
managers_db: Dict[str, Dict] = {
    "default": {"name": "Default Manager", "rating": 0, "total_chats": 0}
}

# Импортируем профессиональный анализатор
# Импортируем профессиональный анализатор
try:
    from analyzer_pro import analyze_chat_pro, convert_to_table_row, get_table_headers, export_to_csv
    logger.info("✅ Professional analyzer loaded")
    
    # Проверяем есть ли функция export_to_excel
    try:
        from analyzer_pro import export_to_excel
    except ImportError:
        # Создаем заглушку если функции нет
        def export_to_excel(analyses, filename):
            return export_to_csv(analyses, filename.replace('.xlsx', '.csv'))
            
except ImportError as e:
    logger.error(f"❌ Failed to load professional analyzer: {e}")
    analyze_chat_pro = None
    # Заглушки для функций
    convert_to_table_row = None
    get_table_headers = None
    export_to_csv = None
    export_to_excel = None

# Импортируем обработчики
from wazzup_handler import WazzupHandler, handle_wazzup_webhook

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
    logger.info("🚀 Starting WABA AI Professional Analyzer Server")
    
    # Проверяем конфигурацию
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("⚠️  OPENAI_API_KEY not set")
    
    if WAZZUP_ENABLED:
        logger.info("✅ Wazzup integration ready")
    
    if analyze_chat_pro:
        logger.info("✅ Professional analyzer ready")
    else:
        logger.error("❌ Professional analyzer not available")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down server")
    save_data_to_file()

def save_data_to_file():
    """Сохраняем данные в файл"""
    try:
        with open("data/chats_backup.json", "w") as f:
            json.dump(chats_db, f, default=str, indent=2)
        with open("data/analyses_pro_backup.json", "w") as f:
            json.dump(analyses_pro_db, f, default=str, indent=2)
        logger.info("💾 Data saved to files")
    except Exception as e:
        logger.error(f"❌ Error saving data: {e}")

def load_data_from_file():
    """Загружаем данные из файла"""
    global chats_db, analyses_pro_db
    try:
        if os.path.exists("data/chats_backup.json"):
            with open("data/chats_backup.json", "r") as f:
                chats_db = json.load(f)
            logger.info(f"📂 Loaded {len(chats_db)} chats from backup")
        
        if os.path.exists("data/analyses_pro_backup.json"):
            with open("data/analyses_pro_backup.json", "r") as f:
                analyses_pro_db = json.load(f)
            logger.info(f"📂 Loaded {len(analyses_pro_db)} professional analyses from backup")
    except Exception as e:
        logger.error(f"❌ Error loading data: {e}")

# Загружаем данные при старте
load_data_from_file()

app = FastAPI(
    title="WABA AI Professional Analyzer",
    version="2.0.0",
    description="Professional AI-powered chat analyzer for quality control with OKC methodology",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
            "tags": [],
            "metadata": {
                "manager_name": message_data.get("manager_name", "Unknown"),
                "channel": message_data.get("channel", "whatsapp"),
                "funnel_stage": message_data.get("funnel_stage", "unknown")
            }
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
    
    logger.info(f"💾 Сообщение сохранено в чат {chat_id}")

@app.get("/")
async def root():
    """Главная страница API"""
    return {
        "status": "online",
        "service": "WABA AI Professional Analyzer",
        "version": "2.0.0",
        "methodology": "ОКК (Отдел Контроля Качества Коммуникаций)",
        "features": "Русские названия колонок, Excel экспорт, Автофильтры",
        "endpoints": {
            "webhook": "POST /webhook/wazzup",
            "chats": "GET /chats",
            "chat_detail": "GET /chats/{chat_id}",
            "analyze_pro": "POST /analyze/pro/{chat_id}",
            "analyze_batch_pro": "POST /analyze/pro/batch",
            "get_analysis_pro": "GET /analysis/pro/{chat_id}",
            "export_csv": "GET /export/csv",
            "export_excel": "GET /export/excel",
            "dashboard_pro": "GET /dashboard/pro",
            "health": "GET /health"
        },
        "integrations": {
            "wazzup": WAZZUP_ENABLED,
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "professional_analyzer": analyze_chat_pro is not None
        },
        "stats": {
            "total_chats": len(chats_db),
            "total_pro_analyses": len(analyses_pro_db),
            "active_chats": len([c for c in chats_db.values() if c.get("status") == "active"])
        }
    }

@app.get("/health")
async def health():
    """Проверка работоспособности"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "api": "healthy",
            "database": "healthy",
            "openai": "configured" if os.getenv("OPENAI_API_KEY") else "not_configured",
            "wazzup": "enabled" if WAZZUP_ENABLED else "disabled",
            "professional_analyzer": "ready" if analyze_chat_pro else "not_available"
        }
    }

@app.post("/webhook/wazzup")
async def wazzup_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Вебхук Wazzup
    """
    try:
        data = await request.json()
        logger.info(f"📨 Wazzup webhook received")

        # Фоновая обработка
        background_tasks.add_task(process_wazzup_webhook, data)

    except Exception as e:
        logger.error(f"❌ Webhook parse error: {e}")

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
    
    except Exception as e:
        logger.error(f"❌ Background processing error: {e}")

@app.get("/chats")
async def get_chats(
    limit: int = 50,
    offset: int = 0,
    status: str = None,
    manager_id: str = None,
    with_analysis: bool = False
):
    """Получить список диалогов"""
    filtered_chats = list(chats_db.values())
    
    # Фильтрация
    if status:
        filtered_chats = [c for c in filtered_chats if c.get("status") == status]
    
    if manager_id:
        filtered_chats = [c for c in filtered_chats if c.get("manager_id") == manager_id]
    
    # Сортировка
    filtered_chats.sort(key=lambda x: x.get("last_updated", ""), reverse=True)
    
    # Пагинация
    paginated = filtered_chats[offset:offset + limit]
    
    # Форматируем ответ
    formatted_chats = []
    for chat in paginated:
        chat_id = chat["id"]
        messages = chat.get("messages", [])
        
        formatted_chats.append({
            "id": chat_id,
            "client_number": chat.get("client_number", "unknown"),
            "manager_id": chat.get("manager_id", "default"),
            "manager_name": chat.get("metadata", {}).get("manager_name", "Unknown"),
            "message_count": len(messages),
            "created_at": chat.get("created_at"),
            "last_updated": chat.get("last_updated"),
            "status": chat.get("status", "active"),
            "has_pro_analysis": chat_id in analyses_pro_db,
            "pro_score": analyses_pro_db.get(chat_id, {}).get("summary_score", 0) if chat_id in analyses_pro_db else None,
            "last_message": messages[-1]["text"][:100] if messages else ""
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
    
    # Форматируем сообщения
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
        "pro_analysis_available": chat_id in analyses_pro_db
    }

@app.post("/analyze/pro/{chat_id}")
async def analyze_chat_pro_endpoint(
    chat_id: str,
    force: bool = False
):
    """Профессиональный анализ диалога по методологии ОКК"""
    if not analyze_chat_pro:
        raise HTTPException(status_code=501, detail="Professional analyzer not available")
    
    if chat_id not in chats_db:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    chat = chats_db[chat_id]
    messages = chat.get("messages", [])
    
    if len(messages) < 2:
        return {"error": "Диалог слишком короткий для анализа", "min_messages": 2}
    
    # Проверяем, не анализировался ли недавно
    if not force and chat_id in analyses_pro_db:
        last_analysis = analyses_pro_db[chat_id].get("analysis_timestamp", "")
        if last_analysis:
            try:
                last_date = datetime.fromisoformat(last_analysis.replace('Z', '+00:00'))
                if (datetime.now() - last_date) < timedelta(minutes=10):
                    return {
                        "warning": "Диалог недавно анализировался",
                        "last_analysis": last_analysis,
                        "use_force": True
                    }
            except:
                pass
    
    try:
        logger.info(f"🔍 Запускаю профессиональный анализ диалога {chat_id}")
        
        # Подготавливаем метаданные
        metadata = {
            "manager": chat.get("metadata", {}).get("manager_name", chat.get("manager_id", "default")),
            "channel": chat.get("metadata", {}).get("channel", "whatsapp"),
            "datetime": chat.get("created_at", ""),
            "funnel_stage": chat.get("metadata", {}).get("funnel_stage", "unknown"),
            "crm_link": f"chat_{chat_id}",
            "chat_id": chat_id
        }
        
        # Запускаем профессиональный анализ
        analysis_result = analyze_chat_pro(messages, metadata)
        
        # Сохраняем результат
        analyses_pro_db[chat_id] = analysis_result
        
        # Обновляем статистику менеджера
        manager_id = chat.get("manager_id", "default")
        if manager_id not in managers_db:
            managers_db[manager_id] = {"name": manager_id, "rating": 0, "total_chats": 0}
        
        managers_db[manager_id]["total_chats"] += 1
        if "summary_score" in analysis_result:
            # Обновляем рейтинг менеджера
            current_rating = managers_db[manager_id].get("rating", 0)
            new_score = analysis_result["summary_score"]
            managers_db[manager_id]["rating"] = (current_rating + new_score) / 2
        
        logger.info(f"✅ Профессиональный анализ завершен. Счет: {analysis_result.get('summary_score', 0)}/100")
        
        # Возвращаем также табличную строку
        table_row = convert_to_table_row(analysis_result, chat_id)
        
        return {
            "status": "success",
            "analysis": analysis_result,
            "table_row": table_row,
            "chat_id": chat_id,
            "score": analysis_result.get("summary_score", 0)
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка профессионального анализа: {e}")
        raise HTTPException(status_code=500, detail=f"Professional analysis failed: {str(e)}")

@app.get("/analysis/pro/{chat_id}")
async def get_pro_analysis(chat_id: str, format: str = "json"):
    """Получить результат профессионального анализа"""
    if chat_id not in analyses_pro_db:
        raise HTTPException(status_code=404, detail="Professional analysis not found")
    
    analysis = analyses_pro_db[chat_id]
    
    if format == "table":
        # Возвращаем табличную строку
        return convert_to_table_row(analysis, chat_id)
    elif format == "csv":
        # Возвращаем как CSV строку
        row = convert_to_table_row(analysis, chat_id)
        headers = get_table_headers()
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers, delimiter=';')
        writer.writeheader()
        writer.writerow(row)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=okc_analysis_{chat_id}.csv"}
        )
    else:
        # Возвращаем полный JSON
        return analysis

@app.post("/analyze/pro/batch")
async def analyze_batch_pro(
    start_date: str = None,
    end_date: str = None,
    manager_id: str = None,
    min_messages: int = 3,
    limit: int = 10,
    force: bool = False
):
    """
    Массовый профессиональный анализ диалогов
    """
    if not analyze_chat_pro:
        raise HTTPException(status_code=501, detail="Professional analyzer not available")
    
    try:
        filtered_chats = []
        
        for chat_id, chat in chats_db.items():
            # Фильтрация по дате
            if start_date:
                chat_date = datetime.fromisoformat(chat.get("created_at", "2000-01-01").replace('Z', '+00:00'))
                start_datetime = datetime.fromisoformat(start_date)
                if chat_date < start_datetime:
                    continue
            
            if end_date:
                chat_date = datetime.fromisoformat(chat.get("created_at", "2000-01-01").replace('Z', '+00:00'))
                end_datetime = datetime.fromisoformat(end_date)
                if chat_date > end_datetime:
                    continue
            
            # Фильтрация по менеджеру
            if manager_id and chat.get("manager_id") != manager_id:
                continue
            
            # Фильтрация по количеству сообщений
            if len(chat.get("messages", [])) < min_messages:
                continue
            
            # Проверяем, не анализировался ли недавно
            if not force and chat_id in analyses_pro_db:
                last_analysis = analyses_pro_db[chat_id].get("analysis_timestamp", "")
                if last_analysis:
                    try:
                        last_date = datetime.fromisoformat(last_analysis.replace('Z', '+00:00'))
                        if (datetime.now() - last_date) < timedelta(hours=12):
                            continue
                    except:
                        pass
            
            filtered_chats.append((chat_id, chat))
        
        # Ограничиваем количество
        filtered_chats = filtered_chats[:limit]
        
        if not filtered_chats:
            return {
                "message": "Нет диалогов по заданным критериям",
                "filters": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "manager_id": manager_id,
                    "min_messages": min_messages,
                    "limit": limit
                },
                "total_chats": len(chats_db)
            }
        
        results = []
        table_rows = []
        
        # Синхронный анализ (может быть долго!)
        for chat_id, chat in filtered_chats:
            try:
                # Подготавливаем метаданные
                metadata = {
                    "manager": chat.get("metadata", {}).get("manager_name", chat.get("manager_id", "default")),
                    "channel": chat.get("metadata", {}).get("channel", "whatsapp"),
                    "datetime": chat.get("created_at", ""),
                    "funnel_stage": chat.get("metadata", {}).get("funnel_stage", "unknown"),
                    "crm_link": f"chat_{chat_id}",
                    "chat_id": chat_id
                }
                
                analysis_result = analyze_chat_pro(chat["messages"], metadata)
                
                # Сохраняем результат
                analyses_pro_db[chat_id] = analysis_result
                
                # Табличная строка
                table_row = convert_to_table_row(analysis_result, chat_id)
                table_rows.append(table_row)
                
                results.append({
                    "chat_id": chat_id,
                    "success": True,
                    "score": analysis_result.get("summary_score", 0),
                    "client": chat.get("client_number", "unknown"),
                    "manager": chat.get("manager_id", "default")
                })
                
                # Небольшая пауза чтобы не перегружать API
                import time
                time.sleep(0.5)
                
            except Exception as e:
                results.append({
                    "chat_id": chat_id,
                    "success": False,
                    "error": str(e)[:100]
                })
        
        # Считаем статистику
        successful = [r for r in results if r["success"]]
        avg_score = sum(r["score"] for r in successful) / len(successful) if successful else 0
        
        return {
            "batch_completed": True,
            "total_analyzed": len(filtered_chats),
            "successful": len(successful),
            "failed": len(results) - len(successful),
            "average_score": round(avg_score, 1),
            "results": results,
            "table_rows": table_rows
        }
    
    except Exception as e:
        logger.error(f"❌ Batch professional analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

@app.get("/export/csv")
async def export_analyses_csv(
    start_date: str = None,
    end_date: str = None,
    manager_id: str = None
):
    """Экспорт всех анализов в CSV с русскими названиями"""
    
    # Фильтруем анализы
    filtered_analyses = []
    for chat_id, analysis in analyses_pro_db.items():
        # Пропускаем ошибки
        if analysis.get("error"):
            continue
        
        # Фильтрация по дате анализа
        if start_date:
            analysis_date = datetime.fromisoformat(analysis.get("analysis_timestamp", "2000-01-01").replace('Z', '+00:00'))
            start_datetime = datetime.fromisoformat(start_date)
            if analysis_date < start_datetime:
                continue
        
        if end_date:
            analysis_date = datetime.fromisoformat(analysis.get("analysis_timestamp", "2000-01-01").replace('Z', '+00:00'))
            end_datetime = datetime.fromisoformat(end_date)
            if analysis_date > end_datetime:
                continue
        
        # Фильтрация по менеджеру
        if manager_id:
            analysis_manager = analysis.get("l0_context", {}).get("manager", "")
            if str(analysis_manager) != str(manager_id):
                continue
        
        filtered_analyses.append(analysis)
    
    if not filtered_analyses:
        raise HTTPException(status_code=404, detail="No analyses found for export")
    
    # Конвертируем в табличные строки
    table_rows = []
    for analysis in filtered_analyses:
        chat_id = analysis.get("chat_id", "unknown")
        table_row = convert_to_table_row(analysis, chat_id)
        table_rows.append(table_row)
    
    # Создаем CSV в памяти
    output = io.StringIO()
    headers = get_table_headers()
    
    writer = csv.DictWriter(output, fieldnames=headers, delimiter=';')
    writer.writeheader()
    writer.writerows(table_rows)
    
    # Генерируем имя файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"okc_аналитика_{timestamp}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/export/excel")
async def export_analyses_excel(
    start_date: str = None,
    end_date: str = None,
    manager_id: str = None
):
    """Экспорт всех анализов в Excel с русскими названиями"""
    
    # Фильтруем анализы
    filtered_analyses = []
    for chat_id, analysis in analyses_pro_db.items():
        # Пропускаем ошибки
        if analysis.get("error"):
            continue
        
        # Фильтрация по дате анализа
        if start_date:
            analysis_date = datetime.fromisoformat(analysis.get("analysis_timestamp", "2000-01-01").replace('Z', '+00:00'))
            start_datetime = datetime.fromisoformat(start_date)
            if analysis_date < start_datetime:
                continue
        
        if end_date:
            analysis_date = datetime.fromisoformat(analysis.get("analysis_timestamp", "2000-01-01").replace('Z', '+00:00'))
            end_datetime = datetime.fromisoformat(end_date)
            if analysis_date > end_datetime:
                continue
        
        # Фильтрация по менеджеру
        if manager_id:
            analysis_manager = analysis.get("l0_context", {}).get("manager", "")
            if str(analysis_manager) != str(manager_id):
                continue
        
        filtered_analyses.append(analysis)
    
    if not filtered_analyses:
        raise HTTPException(status_code=404, detail="No analyses found for export")
    
    # Создаем Excel файл
    try:
        import pandas as pd
        
        # Конвертируем в DataFrame
        rows = []
        for analysis in filtered_analyses:
            chat_id = analysis.get("chat_id", "unknown")
            table_row = convert_to_table_row(analysis, chat_id)
            rows.append(table_row)
        
        df = pd.DataFrame(rows, columns=get_table_headers())
        
        # Создаем Excel в памяти
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Аналитика чатов')
            
            # Добавляем сводный лист
            summary_data = {
                'Метрика': [
                    'Всего чатов',
                    'Средний счет',
                    'Максимальный счет',
                    'Минимальный счет',
                    'Отлично (80-100)',
                    'Хорошо (60-79)',
                    'Удовлетворительно (40-59)',
                    'Требует улучшения (0-39)'
                ],
                'Значение': [
                    len(filtered_analyses),
                    df['Общий счет'].mean(),
                    df['Общий счет'].max(),
                    df['Общий счет'].min(),
                    len(df[df['Общий счет'] >= 80]),
                    len(df[(df['Общий счет'] >= 60) & (df['Общий счет'] < 80)]),
                    len(df[(df['Общий счет'] >= 40) & (df['Общий счет'] < 60)]),
                    len(df[df['Общий счет'] < 40])
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, index=False, sheet_name='Сводка')
        
        output.seek(0)
        
        # Генерируем имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"okc_аналитика_{timestamp}.xlsx"
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ImportError:
        # Если нет pandas/openpyxl, возвращаем CSV
        return await export_analyses_csv(start_date, end_date, manager_id)

@app.get("/dashboard/pro")
async def get_dashboard_pro():
    """Дашборд профессиональной аналитики"""
    
    total_chats = len(chats_db)
    total_analyses = len(analyses_pro_db)
    
    # Собираем статистику по анализам
    scores = []
    managers_stats = {}
    channel_stats = {}
    funnel_stats = {}
    
    for chat_id, analysis in analyses_pro_db.items():
        if analysis.get("error"):
            continue
        
        score = analysis.get("summary_score", 0)
        scores.append(score)
        
        # Статистика по менеджерам
        manager = analysis.get("l0_context", {}).get("manager", "unknown")
        if manager not in managers_stats:
            managers_stats[manager] = {"count": 0, "total_score": 0, "chats": []}
        
        managers_stats[manager]["count"] += 1
        managers_stats[manager]["total_score"] += score
        managers_stats[manager]["chats"].append(chat_id)
        
        # Статистика по каналам
        channel = analysis.get("l0_context", {}).get("channel", "unknown")
        if channel not in channel_stats:
            channel_stats[channel] = {"count": 0, "total_score": 0}
        
        channel_stats[channel]["count"] += 1
        channel_stats[channel]["total_score"] += score
        
        # Статистика по этапам воронки
        funnel = analysis.get("l0_context", {}).get("funnel_stage", "unknown")
        if funnel not in funnel_stats:
            funnel_stats[funnel] = {"count": 0, "total_score": 0}
        
        funnel_stats[funnel]["count"] += 1
        funnel_stats[funnel]["total_score"] += score
    
    # Рассчитываем средние
    avg_score = sum(scores) / len(scores) if scores else 0
    
    # Топ менеджеров
    top_managers = []
    for manager, stats in managers_stats.items():
        avg_manager_score = stats["total_score"] / stats["count"] if stats["count"] > 0 else 0
        top_managers.append({
            "manager": manager,
            "chat_count": stats["count"],
            "average_score": round(avg_manager_score, 1),
            "chat_ids": stats["chats"][:5]  # Первые 5 чатов
        })
    
    # Сортируем по среднему счету
    top_managers.sort(key=lambda x: x["average_score"], reverse=True)
    
    # Распределение по оценкам
    score_distribution = {
        "excellent": len([s for s in scores if s >= 80]),
        "good": len([s for s in scores if 60 <= s < 80]),
        "average": len([s for s in scores if 40 <= s < 60]),
        "poor": len([s for s in scores if s < 40])
    }
    
    # Топ проблем (из missed_opportunities)
    common_problems = {}
    for analysis in analyses_pro_db.values():
        if analysis.get("error"):
            continue
        
        missed = analysis.get("l6_recommendations", {}).get("missed_opportunities", [])
        for problem in missed:
            if problem not in common_problems:
                common_problems[problem] = 0
            common_problems[problem] += 1
    
    top_problems = sorted(common_problems.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Последние анализы
    recent_analyses = []
    for chat_id in list(analyses_pro_db.keys())[-5:]:  # Последние 5
        analysis = analyses_pro_db[chat_id]
        if not analysis.get("error"):
            recent_analyses.append({
                "chat_id": chat_id,
                "score": analysis.get("summary_score", 0),
                "manager": analysis.get("l0_context", {}).get("manager", "unknown"),
                "analyzed_at": analysis.get("analysis_timestamp", ""),
                "final_status": analysis.get("l5_dialog_result", {}).get("final_status", "unknown")
            })
    
    return {
        "overview": {
            "total_chats": total_chats,
            "total_analyses": total_analyses,
            "coverage_percentage": round((total_analyses / total_chats * 100), 1) if total_chats > 0 else 0,
            "average_score": round(avg_score, 1),
            "analysis_timestamp": datetime.now().isoformat()
        },
        "score_distribution": score_distribution,
        "top_managers": top_managers[:5],  # Топ 5
        "channel_performance": [
            {
                "channel": channel,
                "count": stats["count"],
                "average_score": round(stats["total_score"] / stats["count"], 1) if stats["count"] > 0 else 0
            }
            for channel, stats in channel_stats.items()
        ],
        "funnel_performance": [
            {
                "stage": stage,
                "count": stats["count"],
                "average_score": round(stats["total_score"] / stats["count"], 1) if stats["count"] > 0 else 0
            }
            for stage, stats in funnel_stats.items()
        ],
        "common_problems": [{"problem": p[0], "count": p[1]} for p in top_problems],
        "recent_analyses": recent_analyses
    }

@app.get("/debug/pro/table/{chat_id}")
async def debug_pro_table(chat_id: str):
    """Отладка: табличная строка анализа"""
    if chat_id not in analyses_pro_db:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analyses_pro_db[chat_id]
    table_row = convert_to_table_row(analysis, chat_id)
    
    # Красивый вывод в виде таблицы
    import pandas as pd
    
    df = pd.DataFrame([table_row])
    
    return {
        "chat_id": chat_id,
        "table_row": table_row,
        "html_table": df.to_html(index=False),
        "markdown_table": df.to_markdown(index=False)
    }

# Запуск сервера
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "main_pro:app",  # Исправлено для правильного reload
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )