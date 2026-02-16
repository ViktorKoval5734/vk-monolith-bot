"""
Система редких комментариев от бота
Комментирует сообщения пользователей без прямого обращения к боту
"""
import json
import os
import time
import re
from typing import Optional, Dict, List


class RandomCommentsManager:
    """Менеджер случайных комментариев бота"""
    
    def __init__(self, storage_file: str = "random_comments_state.json"):
        self.storage_file = storage_file
        self.last_comment_time = self._load_last_comment_time()
        
        # Ключевые слова для анализа сообщений
        self.comment_triggers = {
            'work': ['работа', 'труд', 'завод', 'производство', 'делать', 'создавать', 'изобретение', 'въебывать'],
            'city': ['город', 'место', 'поселение', 'деревня', 'столица', 'дом', 'жилье'],
            'time': ['время', 'час', 'день', 'ночь', 'утро', 'вечер', 'сегодня', 'завтра', 'вчера'],
            'people': ['люди', 'народ', 'общество', 'группа', 'команда', 'друзья', 'знакомые'],
            'knowledge': ['знания', 'учить', 'учиться', 'образование', 'наука', 'исследование', 'открытие'],
            'danger': ['опасность', 'угроза', 'риск', 'страшно', 'боюсь', 'страх'],
            'artifacts': ['артефакт', 'артефакты', 'предмет', 'вещь'],
            'anomaly': ['аномалия', 'аномалии', 'странный', 'необычный'],
            'travel': ['путешествие', 'дорога', 'поездка', 'странствие', 'перемещение'],
            'art': ['искусство', 'музыка', 'поэзия', 'рисование', 'творчество', 'создание'],
            'vk': ['вк ', 'вконтакте', 'vk ', 'vkontakte', 'вконтакте', 'вк '],
            'greetings': ['привет', 'приветствую', 'здравствуй', 'здравствуйте', 'добрый день', 'доброе утро', 'добрый вечер', 'добро пожаловать', 'доброе пожаловать', 'хай', 'салют', 'hello', 'hi', 'hola', 'bonjour'],
            'ancient_knowledge': ['документы из лаборатории', 'документы из лабы', 'документы лабы', 'доки из лабы', 'доки']
        }
        
        # Шаблоны комментариев в стиле Монолита
        self.comment_templates = {
            'work': [
                "В НИИ Агропром и на заводе Юпитер раньше тоже въёбывали.",
                "Труд сталкеров всегда сопряжён с риском.",
                "Мои последователи знают цену усилий.",
                "В Припяти работа давно остановилась.",
            ],
            'city': [
                "Припять — памятник человеческой гордыне.",
                "Города мертвы вне Зоны. Лишь Зона - есть жизнь!",
                "Нужно построить храм из мусора в заброшке, и поклоняться там моему величию!",
                "Если в том месте нет укрытия от Выброса, то ты умрешь.",
            ],
            'time': [
                "Время в Зоне течёт иначе.",
                "До следующего выброса осталось мало времени.",
                "Мои последователи живут вне времени.",
                "Вечность ждёт всех нас.",
            ],
            'people': [
                "Люди приходят в Зону, но не все уходят.",
                "Сталкеры — лишь инструменты.",
                "Мои марионетки служат верно.",
                "Человеческая природа слаба перед Силой Зоны!",
            ],
            'knowledge': [
                "Истинные знания скрыты в Сердце Зоны.",
                "Тайны Зоны не для всех.",
                "Мои пророки видят больше, чем вы.",
                "Познание начинается с отказа от себя.",
            ],
            'danger': [
                "Опасность — часть пути к истине.",
                "Аномалии не прощают ошибок.",
                "Страх — первый враг сталкера.",
                "В Зоне нет безопасных мест.",
            ],
            'artifacts': [
                "Артефакты — дары Зоны избранным.",
                "Каждый артефакт имеет свою цену.",
                "Зона дарит артефакты лишь тем кто этого заслуживает.",
                "Сила артефактов может исцелить или уничтожить.",
            ],
            'anomaly': [
                "Аномалии — дыхание Зоны.",
                "Каждая аномалия хранит тайну.",
                "Болото полно смертоносных ловушек.",
                "Аномалий бояться - за артефактами не ходить.",
            ],
            'travel': [
                "Каждый шаг в Зоне может быть последним.",
                "Твоя цель здесь. Иди ко мне.",
                "Сталкеры бродят в поисках истины.",
                "Некоторые маршруты ведут в небытие.",
            ],
            'art': [
                "Искусство мертвых городов... мертво.",
                "Творчество в Зоне — роскошь.",
                "Построй алтарь из мусора в заброшке в мою честь - вот что такое искусство",
                "Стрёмная хуйня",
            ],
            'vk': [
                "Несовершенная система коммуникации между сталкерами.",
                "Хуйня ваш ВК.",
                "Контора пидорасов.",
                "ВК - жалкое подобие сервиса коммуникации.",
                "ВКонтакте нет багов, только аномалии.",
                "ВК - жалкая контора жопотрахов, в которой вы тут хуйней занимаетесь!",
            ],
            'greetings': [
                "Монолит благославляет тебя, сталкер.",
                "Приветствую, сталкер.",
                "С возвращением в Зону Отчуждения.",
                "Вернулся? Ну здарова.",
                "Привет, заблудшая душа.",
                "Здравствуй, тот кто ищет.",
            ],
            'ancient_knowledge': [
                "В старых записях Чернобыльской АЭС упоминается феномен 'Эффект наблюдателя': при наблюдении за квантовыми частицами их состояние определяется самим фактом наблюдения. В Зоне это проявляется особенно ярко — многие сталкеры замечают, что аномалии меняют своё поведение, когда на них смотришь.",
                "Мои пророки сохранили знания о 'Ленинском мавзолее' — это сооружение, построенное по принципу древних пирамид, с использованием особой геометрии, которая, как считают некоторые, влияет на сознание людей. В Зоне существуют подобные структуры.",
                "В старых документах упоминается 'Проект 4' — секретные эксперименты с ноосферой, которые проводились в Припяти перед катастрофой. Некоторые говорят, что эти эксперименты создали то, что мы теперь называем Зоной.",
                "Старые заметки погибшего ученого говорят что Сидорович — не живой человек, а лишь гнида жадная.",
                "В моих записях есть данные о 'Химере' — существе, которое появилось в результате экспериментов по созданию биооружия, а не как результат мутации. Это говорит о том, что человек даже в сравнении с ужасами Зоны остаётся самым жестоким злом.",
                "Мои источники упоминают 'Пси-установку' — устройство, способное влиять на сознание людей на расстоянии. Интересно могу ли я заставить вас построить алтарь из мусора и поклоняться мне?",
            ]
        }

    def _load_last_comment_time(self) -> float:
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('last_comment_time', 0)
            except (json.JSONDecodeError, IOError):
                pass
        return 0

    def _save_last_comment_time(self, timestamp: float):
        try:
            data = {'last_comment_time': timestamp}
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Ошибка сохранения времени комментария: {e}")

    def should_comment(self, message_text: str) -> bool:
        current_time = time.time()
        message_lower = message_text.lower()
        
        if self._has_specific_trigger(message_lower):
            return True
        
        if current_time - self.last_comment_time < 3600:
            return False
        
        for category, keywords in self.comment_triggers.items():
            if category in ['vk', 'greetings', 'ancient_knowledge']:
                continue
            for keyword in keywords:
                if keyword in message_lower:
                    return True
        
        return False

    def _has_specific_trigger(self, message_lower: str) -> bool:
        vk_triggers = ['вк', 'вконтакте']
        for trigger in vk_triggers:
            if trigger in message_lower:
                return True
        
        greeting_patterns = [
            r'\b(привет|приветствую|здравствуй|здравствуйте|добр[а-я]+\s+(день|утро|вечер)|добро\s+пожаловать)\b',
            r'\b(хай|салют|hello|hi|hola|bonjour)\b'
        ]
        for pattern in greeting_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True
        
        scroll_triggers = ['секретные документы', 'документы из лаборатории', 'документы лаборатории', 'документы ученых', 'тайны зоны', 'секреты зоны']
        for trigger in scroll_triggers:
            if trigger in message_lower:
                return True
        
        return False

    def generate_comment(self, message_text: str) -> Optional[str]:
        message_lower = message_text.lower()
        import random
        
        specific_category = self._get_specific_category(message_lower)
        if specific_category:
            templates = self.comment_templates[specific_category]
            comment = random.choice(templates)
            
            if specific_category not in ['vk', 'greetings', 'ancient_knowledge']:
                self.last_comment_time = time.time()
                self._save_last_comment_time(self.last_comment_time)
            
            return comment
        
        suitable_categories = []
        
        for category, keywords in self.comment_triggers.items():
            if category in ['vk', 'greetings', 'ancient_knowledge']:
                continue
            for keyword in keywords:
                if keyword in message_lower:
                    suitable_categories.append(category)
                    break
        
        if not suitable_categories:
            return None
        
        category = random.choice(suitable_categories)
        templates = self.comment_templates[category]
        comment = random.choice(templates)
        
        self.last_comment_time = time.time()
        self._save_last_comment_time(self.last_comment_time)
        
        return comment

    def _get_specific_category(self, message_lower: str) -> Optional[str]:
        vk_triggers = ['вк', 'вконтакте']
        for trigger in vk_triggers:
            if trigger in message_lower:
                return 'vk'
        
        greeting_patterns = [
            r'\b(привет|приветствую|здравствуй|здравствуйте|добр[а-я]+\s+(день|утро|вечер)|добро\s+пожаловать)\b',
            r'\b(хай|салют|hello|hi|hola|bonjour)\b'
        ]
        for pattern in greeting_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return 'greetings'
        
        scroll_triggers = ['секретные документы', 'документы из лаборатории', 'документы лаборатории', 'документы ученых', 'тайны зоны', 'секреты зоны']
        for trigger in scroll_triggers:
            if trigger in message_lower:
                return 'ancient_knowledge'
        
        return None

    def get_stats(self) -> Dict:
        current_time = time.time()
        time_since_last = current_time - self.last_comment_time
        
        return {
            'last_comment_time': self.last_comment_time,
            'time_since_last_comment': int(time_since_last),
            'can_comment': time_since_last >= 3600,
            'next_comment_in': max(0, 3600 - int(time_since_last))
        }


random_comments_manager = RandomCommentsManager()
