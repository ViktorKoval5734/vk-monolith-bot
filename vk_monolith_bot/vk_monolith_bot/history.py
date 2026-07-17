"""
Работа с историей переписки (файловое хранилище)
"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from config import HISTORY_LIMIT


class HistoryManager:
    """
    Менеджер истории переписки с сохранением в файл.
    Хранит историю для каждой беседы отдельно.
    """

    def __init__(self, history_file: str = "history.json"):
        self.history_file = history_file
        self.history: Dict[str, List[Dict]] = self._load_history()

    def _load_history(self) -> Dict[str, List[Dict]]:
        """Загрузка истории из файла"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Ошибка загрузки истории: {e}")
                return {}
        return {}

    def _save_history(self):
        """Сохранение истории в файл"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def get_history(self, chat_id: str) -> List[Dict]:
        """Получение истории для конкретной беседы"""
        return self.history.get(chat_id, [])

    def add_message(self, chat_id: str, role: str, content: str):
        """
        Добавление сообщения в историю

        Args:
            chat_id: ID беседы
            role: Роль ('user', 'assistant', 'system')
            content: Текст сообщения
        """
        if chat_id not in self.history:
            self.history[chat_id] = []

        self.history[chat_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

        # Ограничиваем историю до настроенного лимита
        if len(self.history[chat_id]) > HISTORY_LIMIT:
            self.history[chat_id] = self.history[chat_id][-HISTORY_LIMIT:]

        self._save_history()

    def clear_history(self, chat_id: str):
        """Очистка истории конкретной беседы"""
        if chat_id in self.history:
            self.history[chat_id] = []
            self._save_history()

    def get_messages_for_gigachat(self, chat_id: str) -> List[Dict]:
        """
        Получение истории в формате для GigaChat API.
        Убирает технические поля (timestamp).
        """
        history = self.get_history(chat_id)
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in history
        ]


# Глобальный экземпляр
history_manager = HistoryManager()