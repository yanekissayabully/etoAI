import json
import logging
import hashlib
import hmac
from datetime import datetime
from typing import Dict, Any
import os

logger = logging.getLogger(__name__)

# Импортируем глобальное хранилище
from main import chats_db

def verify_webhook(payload: bytes, signature: str) -> bool:
    """Проверка подписи вебхука"""
    secret = os.getenv("WEBHOOK_SECRET", "").encode()
    expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

def handle_waba_webhook(data: Dict[str, Any]):
    """
    Обработчик входящих сообщений из WABA (Ultramsg)
    """
    try:
        # Ultramsg формат: https://docs.ultramsg.com/api/webhook
        message_type = data.get("event")
        
        if message_type == "message":
            # Извлекаем данные сообщения
            from_number = data.get("from")
            to_number = data.get("to")
            message_body = data.get("body", "")
            message_id = data.get("id", "")
            timestamp = data.get("timestamp", int(datetime.now().timestamp()))
            
            logger.info(f"💬 Сообщение от {from_number}: {message_body[:50]}...")
            
            # Создаем ID диалога (обычно номер клиента)
            chat_id = from_number  # или комбинация from+to
            
            # Инициализируем диалог если его нет
            if chat_id not in chats_db:
                chats_db[chat_id] = {
                    "client_number": from_number,
                    "manager_number": to_number,
                    "messages": [],
                    "created_at": datetime.fromtimestamp(timestamp).isoformat(),
                    "last_updated": datetime.fromtimestamp(timestamp).isoformat()
                }
            
            # Определяем отправителя
            if from_number == to_number:
                role = "manager"  # это наш менеджер
            else:
                role = "client"   # это клиент
            
            # Добавляем сообщение
            message_data = {
                "id": message_id,
                "role": role,
                "text": message_body,
                "timestamp": datetime.fromtimestamp(timestamp).isoformat(),
                "raw_data": data
            }
            
            chats_db[chat_id]["messages"].append(message_data)
            chats_db[chat_id]["last_updated"] = datetime.fromtimestamp(timestamp).isoformat()
            
            # Сохраняем в файл для надежности
            with open(f"logs/chat_{chat_id}.json", "w") as f:
                json.dump(chats_db[chat_id], f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Сообщение сохранено в диалог {chat_id}")
            
            # Проверяем, можно ли уже анализировать (есть хотя бы 2 сообщения менеджера)
            manager_messages = [m for m in chats_db[chat_id]["messages"] if m["role"] == "manager"]
            if len(manager_messages) >= 2:
                logger.info(f"📊 Диалог {chat_id} готов для анализа ({len(manager_messages)} сообщений менеджера)")
        
        elif message_type == "status":
            # Статус доставки/прочтения
            logger.info(f"📨 Статус сообщения: {data.get('status')}")
        
        else:
            logger.warning(f"⚠️ Неизвестный тип события: {message_type}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка обработки вебхука: {e}")
        raise