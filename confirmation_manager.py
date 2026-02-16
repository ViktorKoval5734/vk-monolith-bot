"""
Менеджер кода подтверждения для Callback API ВКонтакте
Автоматически определяет и сохраняет правильный код подтверждения
"""
import json
import logging
import os
import time
from typing import Optional

from config import VK_CONFIRMATION_CODE

logger = logging.getLogger(__name__)

class ConfirmationManager:
    def __init__(self, storage_file: str = "confirmation_code.json"):
        self.storage_file = storage_file
        self.expected_code = VK_CONFIRMATION_CODE  # Используем код из конфигурации
        self.last_attempt_time = 0
        self.attempt_count = 0
        self.max_attempts = 5
        self.load_code()
        
        # Если код есть в конфигурации, используем его
        if VK_CONFIRMATION_CODE:
            self.expected_code = VK_CONFIRMATION_CODE
    
    def load_code(self) -> Optional[str]:
        """Загружает код подтверждения из файла"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.expected_code = data.get('code')
                    self.last_attempt_time = data.get('last_attempt', 0)
                    self.attempt_count = data.get('attempt_count', 0)
                    
                    if self.expected_code:
                        logger.info(f"📋 Загружен код подтверждения: {self.expected_code}")
                        return self.expected_code
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки кода подтверждения: {e}")
        
        return None
    
    def save_code(self, code: str) -> bool:
        """Сохраняет код подтверждения в файл"""
        try:
            data = {
                'code': code,
                'last_attempt': int(time.time()),
                'attempt_count': self.attempt_count + 1
            }
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.expected_code = code
            self.last_attempt_time = data['last_attempt']
            self.attempt_count = data['attempt_count']
            
            logger.info(f"💾 Сохранён код подтверждения: {code}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения кода подтверждения: {e}")
            return False
    
    def get_code(self) -> Optional[str]:
        """Возвращает текущий код подтверждения"""
        return self.expected_code
    
    def should_attempt_update(self) -> bool:
        """Проверяет, можно ли попытаться обновить код"""
        current_time = int(time.time())
        
        # Если прошло больше 5 минут с последней попытки
        if current_time - self.last_attempt_time > 300:  # 5 минут
            return True
        
        # Если попыток меньше максимума
        if self.attempt_count < self.max_attempts:
            return True
        
        return False
    
    def record_attempt(self):
        """Записывает попытку обновления кода"""
        self.attempt_count += 1
        self.last_attempt_time = int(time.time())
    
    def reset_attempts(self):
        """Сбрасывает счётчик попыток"""
        self.attempt_count = 0
        logger.info("🔄 Сброшен счётчик попыток обновления кода")
    
    def get_status(self) -> dict:
        """Возвращает статус менеджера"""
        return {
            'has_code': self.expected_code is not None,
            'code': self.expected_code,
            'last_attempt': self.last_attempt_time,
            'attempt_count': self.attempt_count,
            'can_attempt': self.should_attempt_update()
        }
    
    def update_code_from_env(self):
        """Обновляет код из переменной окружения VK_CONFIRMATION_CODE"""
        env_code = os.getenv('VK_CONFIRMATION_CODE')
        if env_code and env_code != self.expected_code:
            self.save_code(env_code)
            logger.info(f"🔄 Код обновлён из переменной окружения: {env_code}")
            return True
        return False
    
    def get_setup_instructions(self) -> str:
        """Возвращает инструкции по настройке кода"""
        current_code = self.get_code()
        if current_code:
            return f"""🔧 Настройка кода подтверждения:

Текущий код: {current_code}

Для обновления кода:
1. В настройках Callback API ВКонтакте скопируйте новый код подтверждения
2. Обновите переменную окружения VK_CONFIRMATION_CODE={current_code}
3. Перезапустите бота

Или создайте файл .env с:
VK_CONFIRMATION_CODE={current_code}

Статус: {'✅ Настроен' if current_code else '❌ Не настроен'}"""
        else:
            return """🔧 Настройка кода подтверждения:

❌ Код подтверждения не настроен!

Для настройки:
1. В настройках Callback API ВКонтакте при настройке будет показан код подтверждения
2. Скопируйте его и создайте файл .env:
   VK_CONFIRMATION_CODE=ваш_код_здесь
3. Перезапустите бота

После первого запуска с корректным кодом он будет автоматически сохранён."""

# Глобальный экземпляр менеджера
confirmation_manager = ConfirmationManager()