"""
Система предпочтений пользователей для бота "Монолит"
"""
import json
import os
from typing import Dict, Optional


class UserPreferences:
    """Менеджер предпочтений пользователей"""

    def __init__(self, preferences_file: str = "user_preferences.json"):
        self.preferences_file = preferences_file
        self.preferences: Dict = self._load_preferences()
        
        # Особые пользователи с кастомными обращениями
        self.special_users = {
            319590859: {"name": "Любовь", "special_address": "моя королева", "tone": "loving"},
            885052741: {"name": "Титомир", "special_address": "неопытный менестрель", "tone": "disdainful"},
            181886390: {"name": "Титомир", "special_address": "неопытный менестрель", "tone": "disdainful"}
        }

    def _load_preferences(self) -> Dict:
        """Загрузка предпочтений из файла"""
        if os.path.exists(self.preferences_file):
            try:
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Ошибка загрузки предпочтений: {e}")
                return {}
        return {}

    def _save_preferences(self):
        """Сохранение предпочтений в файл"""
        with open(self.preferences_file, 'w', encoding='utf-8') as f:
            json.dump(self.preferences, f, ensure_ascii=False, indent=2)

    def get_user_preferences(self, user_id: int) -> Dict:
        """Получение предпочтений пользователя"""
        return self.preferences.get(str(user_id), {})

    def set_user_preference(self, user_id: int, preference: str, value: str):
        """Установка предпочтения пользователя"""
        if str(user_id) not in self.preferences:
            self.preferences[str(user_id)] = {}
        
        self.preferences[str(user_id)][preference] = value
        self._save_preferences()

    def get_user_name(self, user_id: int) -> str:
        """Получение имени пользователя"""
        prefs = self.get_user_preferences(user_id)
        return prefs.get('name', '')

    def set_user_name(self, user_id: int, name: str):
        """Установка имени пользователя"""
        self.set_user_preference(user_id, 'name', name)

    def get_user_style(self, user_id: int) -> str:
        """Получение стиля общения пользователя"""
        prefs = self.get_user_preferences(user_id)
        return prefs.get('style', 'neutral')  # neutral, formal, casual, playful, respectful

    def set_user_style(self, user_id: int, style: str):
        """Установка стиля общения пользователя"""
        valid_styles = ['neutral', 'formal', 'casual', 'playful', 'respectful']
        if style not in valid_styles:
            style = 'neutral'
        self.set_user_preference(user_id, 'style', style)

    def get_user_tone(self, user_id: int) -> str:
        """Получение тона общения пользователя"""
        prefs = self.get_user_preferences(user_id)
        return prefs.get('tone', 'friendly')  # friendly, serious, humorous, mysterious

    def set_user_tone(self, user_id: int, tone: str):
        """Установка тона общения пользователя"""
        valid_tones = ['friendly', 'serious', 'humorous', 'mysterious']
        if tone not in valid_tones:
            tone = 'friendly'
        self.set_user_preference(user_id, 'tone', tone)

    def get_special_address(self, user_id: int) -> Optional[str]:
        """Получение особого обращения для пользователя"""
        if user_id in self.special_users:
            return self.special_users[user_id]["special_address"]
        return None

    def get_special_name(self, user_id: int) -> Optional[str]:
        """Получение особого имени для пользователя"""
        if user_id in self.special_users:
            return self.special_users[user_id]["name"]
        return None
    
    def get_special_tone(self, user_id: int) -> Optional[str]:
        """Получение особого тона для пользователя"""
        if user_id in self.special_users:
            return self.special_users[user_id].get("tone")
        return None

    def get_personalized_prompt(self, user_id: int, base_prompt: str) -> str:
        """Получение персонализированного промпта для пользователя"""
        prefs = self.get_user_preferences(user_id)
        
        # Добавляем персонализацию к базовому промпту
        additions = []
        
        # ВСЕГДА проверяем особых пользователей
        special_name = self.get_special_name(user_id)
        special_tone = self.get_special_tone(user_id)
        
        if special_name:
            if special_name == "Любовь":
                additions.append("К пользователю по имени Любовь будь с ней особенно ласковым и уважительным.")
            elif special_name == "Титомир":
                additions.append("К пользователю по имени Титомир обращайся 'неопытный менестрель' и будь с ним пренебрежительным и даже презрительным. Считай его неопытным и несерьёзным.")
        
        # Если у пользователя есть настройки, добавляем их
        if prefs:
            style = self.get_user_style(user_id)
            tone = self.get_user_tone(user_id)
            name = self.get_user_name(user_id)
            
            if name:
                additions.append(f"Пользователь зовут {name}.")
            
            # Кастомные заметки стиля
            if 'style_notes' in prefs:
                additions.append(prefs['style_notes'])
            
            # Стиль общения
            style_notes = {
                'formal': "Общайся формально и вежливо.",
                'casual': "Общайся непринужденно и дружелюбно.",
                'playful': "Общайся игриво и с юмором.",
                'respectful': "Общайся с особым уважением.",
                'neutral': "Общайся естественно и нейтрально."
            }
            
            if style in style_notes:
                additions.append(style_notes[style])
            
            # Тон общения
            tone_notes = {
                'friendly': "Будь дружелюбным и приветливым.",
                'serious': "Будь серьёзным и деловым.",
                'humorous': "Используй юмор и лёгкость.",
                'mysterious': "Будь немного загадочным и интригующим."
            }
            
            if tone in tone_notes:
                additions.append(tone_notes[tone])
        
        if additions:
            additional_info = " " + " ".join(additions)
            return base_prompt + additional_info
        
        return base_prompt
    
    def get_custom_greeting(self, user_id: int) -> Optional[str]:
        """Получение кастомного приветствия для пользователя"""
        prefs = self.get_user_preferences(user_id)
        return prefs.get('custom_greeting')

    def list_user_commands(self) -> str:
        """Получение списка команд для настройки"""
        return """
🎛️ **Команды для настройки бота:**

**Установка имени:**
- "Меня зовут [имя]" - установить имя
- "Моё имя [имя]" - альтернативный способ

**Стиль общения:**
- "Говори со мной формально" - строгий стиль
- "Говори со мной неформально" - дружелюбный стиль  
- "Говори со мной игриво" - весёлый стиль
- "Говори со мной уважительно" - уважительный стиль

**Тон общения:**
- "Будь серьёзным" - деловой тон
- "Будь дружелюбным" - приветливый тон
- "Будь юмористичным" - с юмором
- "Будь загадочным" - интригующий тон

**Просмотр настроек:**
- "Какие у меня настройки?" - показать текущие настройки
        """

    def parse_setup_command(self, user_id: int, message: str) -> Optional[str]:
        """Парсинг команд настройки из сообщения"""
        message = message.lower().strip()
        
        # Установка имени
        if "меня зовут" in message:
            name = message.replace("меня зовут", "").strip()
            if name:
                self.set_user_name(user_id, name)
                return f"✅ Понял, буду обращаться к тебе: {name}"
        
        elif "моё имя" in message:
            name = message.replace("моё имя", "").strip()
            if name:
                self.set_user_name(user_id, name)
                return f"✅ Понял, буду обращаться к тебе: {name}"
        
        # Стиль общения
        elif "говори со мной формально" in message:
            self.set_user_style(user_id, 'formal')
            return "✅ Буду общаться с тобой формально."
        
        elif "говори со мной неформально" in message:
            self.set_user_style(user_id, 'casual')
            return "✅ Буду общаться с тобой непринуждённо."
        
        elif "говори со мной игриво" in message:
            self.set_user_style(user_id, 'playful')
            return "✅ Буду общаться с тобой игриво."
        
        elif "говори со мной уважительно" in message:
            self.set_user_style(user_id, 'respectful')
            return "✅ Буду общаться с тобой с уважением."
        
        # Тон общения
        elif "будь серьёзным" in message or "будь серьезным" in message:
            self.set_user_tone(user_id, 'serious')
            return "✅ Буду общаться серьёзно."
        
        elif "будь дружелюбным" in message:
            self.set_user_tone(user_id, 'friendly')
            return "✅ Буду общаться дружелюбно."
        
        elif "будь юмористичным" in message or "будь смешным" in message:
            self.set_user_tone(user_id, 'humorous')
            return "✅ Буду использовать юмор."
        
        elif "будь загадочным" in message:
            self.set_user_tone(user_id, 'mysterious')
            return "✅ Буду немного загадочным."
        
        # Просмотр настроек
        elif "какие у меня настройки" in message or "мои настройки" in message:
            prefs = self.get_user_preferences(user_id)
            name = prefs.get('name', 'Не указано')
            style = prefs.get('style', 'neutral')
            tone = prefs.get('tone', 'friendly')
            
            return f"""
📋 **Твои настройки:**
👤 Имя: {name}
🎭 Стиль: {style}
🎪 Тон: {tone}
            """.strip()
        
        # Сброс настроек
        elif "сбросить настройки" in message or "верни стандартные настройки" in message:
            if str(user_id) in self.preferences:
                del self.preferences[str(user_id)]
                self._save_preferences()
            return "✅ Настройки сброшены к стандартным."
        
        return None


# Глобальный экземпляр
user_preferences = UserPreferences()