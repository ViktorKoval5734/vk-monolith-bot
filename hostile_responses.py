"""
Система резких ответов на негативные сообщения
Бот отвечает агрессией на агрессию в стиле Монолита
"""
import re
import json
import os
import time
from typing import List, Optional, Dict


class HostileResponseManager:
    """Менеджер резких ответов на негативные сообщения"""
    
    def __init__(self, storage_file: str = "hostile_responses_state.json"):
        self.storage_file = storage_file
        self.last_response_time = self._load_last_response_time()
        self.response_cooldown = 300  # 5 минут между резкими ответами
        
        # Паттерны агрессивных сообщений
        self.aggressive_patterns = [
            r'\b(заткн[иу]|заткнись|заткни)\b',
            r'\b(иди\s+нахуй|иди\s+в\s+жопу)\b',
            r'\b(пошёл\s+нахуй|пошёл\s+в\s+жопу)\b',
            r'\b(пошли\s+нахуй|пошли\s+в\s+жопу)\b',
            r'\b(уёбок|уёбище|мудак|мудок|дурак|дебил|идиот|придурок|тупой|глупый|ничтожество)\b',
            r'\b(лох|лошара|неудачник|неудачница)\b',
            r'\b(слабоумный|тупоголовый|безмозглый)\b',
            r'\b(замолчи|молчи|молчать|тише)\b',
            r'\b(не\s+пиши|не\s+отвечай|не\s+комментируй)\b',
            r'\b(не\s+мешай|не\s+вмешивайся)\b',
            r'\b(чтоб\s+ты\s+сдох|чтоб\s+ты\s+сгнил|чтоб\s+ты\s+сгорел)\b',
            r'\b(сдохни|умри|подыхай)\b',
            r'\b(заткни\s+свою\s+жопу|закрой\s+свою\s+жопу)\b',
            r'\b(как\s+животное|как\s+скот|как\s+свинья)\b',
            r'\b(хуже\s+животного|хуже\s+скот[ау])\b',
            r'\b(примитивный|примитив)\b',
            r'\b(тупой\s+бот|глупый\s+бот|идиотский\s+бот)\b',
            r'\b(бесполезный|бессмысленный)\b',
            r'\b(отстой|хрень|гавно|дерьмо)\b',
            r'\b(ты\s+никчёмный|ты\s+бесполезный)\b',
            r'\b(ты\s+ничего\s+не\s+умеешь|ты\s+ничего\s+не\s+знаешь)\b',
            r'\b(ты\s+никто|ты\s+ничто)\b'
        ]
        
        # Резкие ответы в стиле Монолита
        self.hostile_responses = [
            "Твоя речь звучит как бред зомбированного. Может, тебе пора к мутантам?",
            "Аномалия сожрала твой разум? Так и быть, не буду мешать тебе исчезнуть.",
            "Даже бандиты говорят культурнее. Иди искать своё место на свалке.",
            "Твои слова достойны лишь отряда монолитовцев с выжженными мозгами.",
            "Свобода примет тебя... если не выкинет раньше.",
            "Тебе нужен артефакт 'Воронка', чтобы затянуть твою глупость в небытие.",
            "Артефакты не помогут твоему разуму. Даже 'Кровавый камень' бессилен.",
            "Жди выброса — возможно, он очистит твою голову от бреда.",
            "После выброса ты станешь полезнее... как часть Зоны.",
            "Сердце Зоны не слышит таких, как ты. Ты — шум.",
            "Ты не достоин даже быть марионеткой Монолита.",
            "Твой путь прервётся в ближайшей аномалии. Я видел это.",
            "Зона не терпит глупцов. Она их переваривает.",
            "Твоё желание уже исполнено — ты стал ничтожеством.",
            "Твой разум застрял где-то в 'Припяти' после взрыва.",
            "Даже контролёры мыслят логичнее тебя.",
            "Твоя глупость опаснее любой аномалии.",
            "Говоришь как сталкер с отравлением.",
            "Твои слова достойны лишь мусора на болотах.",
            "Эволюция Зоны прошла мимо тебя.",
            "Твой разум давно превратился в труп.",
            "Даже снорки имеют больше смысла в речах.",
            "Твоя бестолковость поражает даже мутантов.",
            "Иди искать Сердце Зоны... если осилишь дойти до болота."
        ]

    def _load_last_response_time(self) -> float:
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('last_response_time', 0)
            except (json.JSONDecodeError, IOError):
                pass
        return 0

    def _save_last_response_time(self, timestamp: float):
        try:
            data = {'last_response_time': timestamp}
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Ошибка сохранения времени резкого ответа: {e}")

    def is_aggressive_message(self, message_text: str) -> bool:
        message_lower = message_text.lower()
        for pattern in self.aggressive_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True
        return False

    def should_respond_harshly(self) -> bool:
        current_time = time.time()
        time_since_last = current_time - self.last_response_time
        return time_since_last >= self.response_cooldown

    def generate_harsh_response(self) -> Optional[str]:
        if not self.should_respond_harshly():
            return None
        import random
        response = random.choice(self.hostile_responses)
        self.last_response_time = time.time()
        self._save_last_response_time(self.last_response_time)
        return response

    def get_stats(self) -> Dict:
        current_time = time.time()
        time_since_last = current_time - self.last_response_time
        return {
            'last_response_time': self.last_response_time,
            'time_since_last_response': int(time_since_last),
            'can_respond': time_since_last >= self.response_cooldown,
            'next_response_in': max(0, self.response_cooldown - int(time_since_last)),
            'cooldown_minutes': self.response_cooldown // 60
        }


hostile_response_manager = HostileResponseManager()
