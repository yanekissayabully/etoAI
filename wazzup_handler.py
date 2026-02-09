import requests
import json
import logging
import hashlib
import hmac
from typing import Dict, Any, Optional, List
import os
from datetime import datetime
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class WazzupHandler:
    """Обработчик для Wazzup API"""
    
    def __init__(self):
        self.api_key = os.getenv("WAZZUP_API_KEY")
        self.channel_id = os.getenv("WAZZUP_CHANNEL_ID")
        self.base_url = os.getenv("WAZZUP_API_URL", "https://api.wazzup.io/api")
        
        if not self.api_key:
            logger.warning("⚠️  WAZZUP_API_KEY not set in environment")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        logger.info(f"🔧 WazzupHandler initialized. Channel: {self.channel_id}")
    
    def test_connection(self) -> Dict[str, Any]:
        """Тестирование подключения к Wazzup API"""
        try:
            url = urljoin(self.base_url, "channels")
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                channels = response.json()
                logger.info(f"✅ Wazzup connection successful. Channels: {len(channels)}")
                
                # Автоматически находим WhatsApp канал если не указан
                if not self.channel_id and channels:
                    whatsapp_channels = [
                        c for c in channels 
                        if c.get("type") == "whatsapp" and c.get("active")
                    ]
                    if whatsapp_channels:
                        self.channel_id = whatsapp_channels[0].get("id")
                        logger.info(f"📱 Auto-selected WhatsApp channel: {self.channel_id}")
                
                return {
                    "success": True,
                    "channels": len(channels),
                    "whatsapp_channels": len([c for c in channels if c.get("type") == "whatsapp"]),
                    "channel_id": self.channel_id
                }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"❌ Wazzup connection failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "status_code": response.status_code
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Wazzup connection error: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ Unexpected error testing Wazzup: {e}")
            return {"success": False, "error": str(e)}
    
    def setup_webhook(self, webhook_url: str, events: List[str] = None) -> Dict[str, Any]:
        """Настройка вебхука в Wazzup"""
        try:
            if events is None:
                events = ["message", "message.status", "chat.closed"]
            
            url = urljoin(self.base_url, "webhook")
            payload = {
                "url": webhook_url,
                "events": events,
                "active": True
            }
            
            logger.info(f"🔧 Setting up webhook: {webhook_url}")
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"✅ Webhook configured successfully: {result.get('id')}")
                return {"success": True, "result": result}
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"❌ Webhook setup failed: {error_msg}")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            logger.error(f"❌ Error setting up webhook: {e}")
            return {"success": False, "error": str(e)}
    
    def send_message(self, chat_id: str, text: str, message_type: str = "text") -> Dict[str, Any]:
        """Отправить сообщение через Wazzup"""
        try:
            if not self.channel_id:
                return {"success": False, "error": "Channel ID not configured"}
            
            url = urljoin(self.base_url, "message")
            payload = {
                "channelId": self.channel_id,
                "chatId": chat_id,
                "text": text,
                "type": message_type
            }
            
            logger.info(f"📤 Sending message to {chat_id}: {text[:50]}...")
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Message sent: {result.get('id')}")
                return {"success": True, "result": result}
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"❌ Message sending failed: {error_msg}")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            logger.error(f"❌ Error sending message: {e}")
            return {"success": False, "error": str(e)}
    
    def get_chat_history(self, chat_id: str, limit: int = 100, offset: int = 0) -> Optional[List[Dict]]:
        """Получить историю диалога"""
        try:
            url = urljoin(self.base_url, f"chat/{chat_id}/messages")
            params = {
                "limit": limit,
                "offset": offset
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get("messages", [])
                logger.info(f"📜 Retrieved {len(messages)} messages for chat {chat_id}")
                return messages
            else:
                logger.error(f"❌ Failed to get chat history: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting chat history: {e}")
            return None
    
    def get_chats(self, limit: int = 50, offset: int = 0) -> Optional[List[Dict]]:
        """Получить список чатов"""
        try:
            url = urljoin(self.base_url, "chats")
            params = {"limit": limit, "offset": offset}
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                chats = response.json()
                logger.info(f"📋 Retrieved {len(chats)} chats from Wazzup")
                return chats
            else:
                logger.error(f"❌ Failed to get chats: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting chats: {e}")
            return None

def process_wazzup_message(data: Dict[str, Any]) -> Dict[str, Any]:
    """Обработка сообщения из Wazzup вебхука"""
    try:
        event_type = data.get("type")
        message_data = data.get("message", {})
        
        # Определяем тип события
        if event_type == "message":
            # Новое сообщение
            sender = message_data.get("sender", {})
            chat_id = message_data.get("chatId")
            
            # Определяем роль отправителя
            sender_type = sender.get("type", "")
            if sender_type == "operator":
                role = "manager"
            elif sender_type == "contact":
                role = "client"
            else:
                role = "unknown"
            
            result = {
                "event": "message",
                "chat_id": chat_id,
                "message_id": message_data.get("id"),
                "text": message_data.get("text", ""),
                "role": role,
                "sender": sender,
                "timestamp": message_data.get("timestamp"),
                "raw_data": data
            }
            
            logger.info(f"📨 New {role} message in chat {chat_id}")
            
        elif event_type == "message.status":
            # Статус сообщения
            result = {
                "event": "status",
                "message_id": data.get("messageId"),
                "status": data.get("status"),
                "timestamp": data.get("timestamp"),
                "raw_data": data
            }
            
            logger.info(f"📨 Message status update: {data.get('status')}")
            
        elif event_type == "chat.closed":
            # Чат закрыт
            result = {
                "event": "chat_closed",
                "chat_id": data.get("chatId"),
                "timestamp": data.get("timestamp"),
                "raw_data": data
            }
            
            logger.info(f"📨 Chat closed: {data.get('chatId')}")
            
        else:
            # Неизвестное событие
            result = {
                "event": "unknown",
                "raw_data": data
            }
            
            logger.warning(f"⚠️ Unknown Wazzup event: {event_type}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error processing Wazzup message: {e}")
        return {
            "event": "error",
            "error": str(e),
            "raw_data": data
        }

def handle_wazzup_webhook(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler под Wazzup API v3
    """
    # Тестовый webhook
    if data.get("test"):
        return {"event": "test"}

    messages = data.get("messages", [])
    if not messages:
        return {"event": "empty"}

    msg = messages[0]

    is_inbound = msg.get("status") == "inbound"
    role = "client" if is_inbound else "manager"

    return {
        "event": "message",
        "chat_id": msg.get("chatId"),
        "message_id": msg.get("messageId"),
        "text": msg.get("text", ""),
        "role": role,
        "timestamp": msg.get("dateTime"),
        "sender": msg.get("contact", {}),
        "raw": msg
    }


# Глобальный экземпляр
wazzup_handler = WazzupHandler()

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Проверка подписи вебхука (если используется)"""
    try:
        expected = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)
    except:
        return False