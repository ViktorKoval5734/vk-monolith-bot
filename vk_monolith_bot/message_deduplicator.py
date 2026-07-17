"""
Система дедупликации сообщений для бота ВКонтакте
Предотвращает обработку одного и того же сообщения несколько раз
"""
import time
import hashlib
import logging
from typing import Set, Dict, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

class MessageDeduplicator:
    def __init__(self, max_age: int = 300):  # 5 минут
        self.max_age = max_age  # Время жизни записи в секундах
        self.processed_messages: Dict[int, float] = {}  # message_id -> timestamp
        self.processed_hashes: Dict[str, float] = {}  # content_hash -> timestamp
        self.cleanup_interval = 60  # Очищаем каждые 60 секунд
        self.last_cleanup = time.time()
    
    def _generate_content_hash(self, text: str, user_id: int, peer_id: int) -> str:
        """Генерирует хеш содержимого сообщения"""
        content = f"{text}_{user_id}_{peer_id}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def is_duplicate(self, message_id: int = None, text: str = "", user_id: int = None, peer_id: int = None) -> Tuple[bool, str]:
        """
        Проверяет, было ли уже обработано сообщение
        
        Args:
            message_id: ID сообщения ВКонтакте (если доступен)
            text: Текст сообщения
            user_id: ID пользователя
            peer_id: ID чата/беседы
            
        Returns:
            Tuple[bool, str]: (is_duplicate, reason)
        """
        current_time = time.time()
        
        # Очистка старых записей
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_entries()
            self.last_cleanup = current_time
        
        # Сначала проверяем по ID сообщения (наиболее надёжный способ)
        if message_id and message_id in self.processed_messages:
            return True, f"duplicate_id_{message_id}"
        
        # Если ID недоступен, проверяем по хешу содержимого
        if text and user_id and peer_id:
            content_hash = self._generate_content_hash(text, user_id, peer_id)
            if content_hash in self.processed_hashes:
                return True, f"duplicate_content_{content_hash[:8]}"
            
            # Добавляем хеш в обработанные
            self.processed_hashes[content_hash] = current_time
        
        # Добавляем ID в обработанные (если есть)
        if message_id:
            self.processed_messages[message_id] = current_time
        
        return False, "new_message"
    
    def _cleanup_old_entries(self):
        """Удаляет записи старше max_age секунд"""
        current_time = time.time()
        expired_ids = []
        
        for msg_id, timestamp in self.processed_messages.items():
            if current_time - timestamp > self.max_age:
                expired_ids.append(msg_id)
        
        for msg_id in expired_ids:
            del self.processed_messages[msg_id]
        
        if expired_ids:
            logger.info(f"🧹 Очищено {len(expired_ids)} старых записей сообщений")
    
    def get_stats(self) -> Dict:
        """Возвращает статистику дедупликатора"""
        current_time = time.time()
        active_id_count = len(self.processed_messages)
        active_hash_count = len(self.processed_hashes)
        
        return {
            'active_message_ids': active_id_count,
            'active_content_hashes': active_hash_count,
            'total_active': active_id_count + active_hash_count,
            'max_age_seconds': self.max_age,
            'cleanup_interval_seconds': self.cleanup_interval,
            'last_cleanup': self.last_cleanup,
            'memory_usage_ids': f"{len(str(self.processed_messages))} символов",
            'memory_usage_hashes': f"{len(str(self.processed_hashes))} символов"
        }
    
    def reset(self):
        """Сбрасывает все записи (для тестирования)"""
        self.processed_messages.clear()
        logger.info("🔄 Дедупликатор сброшен")

# Глобальный экземпляр дедупликатора
message_deduplicator = MessageDeduplicator()