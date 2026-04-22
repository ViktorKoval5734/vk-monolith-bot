"""
Система комментариев от бота только на приветствия
Комментирует сообщения с приветствиями
"""
import json
import os
import time
import re
from typing import Optional, Dict, List


class RandomCommentsManager:
    """Менеджер комментариев на приветствия"""
    
    def __init__(self, storage_file: str = "random_comments_state.json"):
        self.storage_file = storage_file
        
        # Только триггер на приветствия
        self.comment_triggers = {
            'greetings': ['привет', 'приветствую', 'здравствуй', 'здравствуйте', 'добрый день', 'доброе утро', 'добрый вечер', 'добро пожаловать', 'доброе пожаловать', 'хай', 'салют', 'hello', 'hi', 'hola', 'bonjour']
        }
        
        # Только шаблоны для приветствий
        self.comment_templates = {
            'greetings': [
                "Монолит благославляет тебя, сталкер.",
                "Приветствую, сталкер.",
                "С возвращением в Зону Отчуждения.",
                "Вернулся? Ну здарова.",
                "Привет, заблудшая душа.",
                "Здравствуй, тот кто ищет."
            ]
        }

    def should_comment(self, message_text: str) -> bool:
        """Проверяет, содержит ли сообщение приветствие"""
        message_lower = message_text.lower()
        return self._has_greeting(message_lower)
    
    def _has_greeting(self, message_lower: str) -> bool:
        """Проверяет наличие приветствия в сообщении"""
        greeting_patterns = [
            r'\b(привет|приветствую|здравствуй|здравствуйте|добр[а-я]+s+(день|утро|вечер)|доброs+пожаловать)\b',
            r'\b(хай|салют|hello|hi|hola|bonjour)\b'
        ]
        for pattern in greeting_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True
        return False

    def generate_comment(self, message_text: str) -> Optional[str]:
        """Генерирует комментарий на приветствие"""
        message_lower = message_text.lower()
        import random
        
        if self._has_greeting(message_lower):
            templates = self.comment_templates['greetings']
            return random.choice(templates)
        
        return None

    def get_stats(self) -> Dict:
        """Статистика (упрощена)"""
        return {
            'triggers_active': ['greetings'],
            'templates_count': len(self.comment_templates['greetings'])
        }


random_comments_manager = RandomCommentsManager()
