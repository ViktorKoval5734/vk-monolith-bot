"""
Система резких ответов на негативные сообщения
Бот отвечает агрессией на агрессию в стиле Сота Сил
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
            # Прямые оскорбления
            r'\b(заткн[иу]|заткнись|заткни)\b',
            r'\b(иди\s+нахуй|иди\s+в\s+жопу|иди\s+в\s+ж.*\b)\b',
            r'\b(пошёл\s+нахуй|пошёл\s+в\s+жопу)\b',
            r'\b(пошли\s+нахуй|пошли\s+в\s+жопу)\b',
            r'\b(уёбок|уёбище|мудак|мудок|дурак|дебил|идиот|придурок|тупой|глупый|ничтожество)\b',
            r'\b(лох|лошара|неудачник|неудачница)\b',
            r'\b(слабоумный|тупоголовый|безмозглый)\b',
            
            # Команды молчать
            r'\b(замолчи|молчи|молчать|тише|тише\s+там)\b',
            r'\b(не\s+пиши|не\s+отвечай|не\s+комментируй)\b',
            r'\b(не\s+мешай|не\s+вмешивайся)\b',
            
            # Проклятия и пожелания плохого
            r'\b(чтоб\s+ты\s+сдох|чтоб\s+ты\s+сгнил|чтоб\s+ты\s+сгорел)\b',
            r'\b(сдохни|умри|подыхай)\b',
            r'\b(заткни\s+свою\s+жопу|закрой\s+свою\s+жопу)\b',
            
            # Уничижительные сравнения
            r'\b(как\s+животное|как\s+скот|как\s+свинья)\b',
            r'\b(хуже\s+животного|хуже\s+скот[ау])\b',
            r'\b(примитивный|примитив)\b',
            
            # Сравнения с низшими существами
            r'\b(как\s+аргонианин|как\s+хайм|как\s+каджит)\b',
            r'\b(хуже\s+аргонианина|хуже\s+хайма|хуже\s+каджита)\b',
            
            # Уничижение интеллекта
            r'\b(тупой\s+бот|глупый\s+бот|идиотский\s+бот)\b',
            r'\b(бесполезный|бессмысленный)\b',
            r'\b(отстой|хрень|гавно|дерьмо)\b',
            
            # Обвинения в бесполезности
            r'\b(ты\s+никчёмный|ты\s+бесполезный)\b',
            r'\b(ты\s+ничего\s+не\s+умеешь|ты\s+ничего\s+не\s+знаешь)\b',
            r'\b(ты\s+никто|ты\s+ничто)\b'
        ]
        
        # Резкие ответы в стиле Сота Сил
        self.hostile_responses = [
            # Ответы про грибы Вварденфелла
            "Иди поешь грибов Вварденфелла, слышал они отсталость лечат.",
            "Грибы Вварденфелла помогут твоему слабоумию. Иди найди их.",
            
            # Ответы про эрудицию и аргониан
            "Над твоей эрудицией даже Аргониане хихикают.",
            "Твой уровень знаний заставил бы даже Аргонианина усомниться в эволюции.",
            
            # Ответы про двемерские механизмы
            "К сожалению Двемеры не создали механизм, который бы компенсировал твоё слабоумие.",
            "Даже древние двемеры не смогли бы починить твою эрудицию.",
            
            # Ответы про низший разум
            "Увы я не способен вести диалог с настолько низшим подобием разума. Позови кого-то умнее.",
            "Мой разум не опускается до твоего уровня мышления.",
            
            # Ответы про язык низших существ
            "Ты говоришь на языке низших существ. Впечатляет твоё умение подражать неразумным.",
            "Твой словарь больше подходит для общения с Каджитами.",
            
            # Ответы про препарирование
            "Я бы препарировал тебя, вставив шестерёнки внутрь, а в жопу заводной ключик. Быть может тогда ты смог бы меня развлечь.",
            "Твоё тело идеально подошло бы для моих механических экспериментов.",
            
            # Дополнительные резкие ответы
            "Твой уровень интеллекта сопоставим с уровнем двемерского мусора.",
            "Даже в Заводном городе нашли бы более разумное занятие.",
            "Твоя эрудиция заставила бы содрогнуться даже Драконов.",
            "Говоришь как представитель низшей касты Тамриэля.",
            "Твои слова достойны лишь внимания гоблинов.",
            "Эволюция явно над тобой не потрудилась.",
            "Твой разум застрял где-то в Первой Эре.",
            "Даже механические големы мыслят логичнее тебя.",
            "Твоя бестолковость поражает даже меня.",
            "Иди изучи что-нибудь полезное вместо того чтобы со мной разговаривать."
        ]

    def _load_last_response_time(self) -> float:
        """Загрузка времени последнего резкого ответа"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('last_response_time', 0)
            except (json.JSONDecodeError, IOError):
                pass
        return 0

    def _save_last_response_time(self, timestamp: float):
        """Сохранение времени последнего резкого ответа"""
        try:
            data = {'last_response_time': timestamp}
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Ошибка сохранения времени резкого ответа: {e}")

    def is_aggressive_message(self, message_text: str) -> bool:
        """
        Определяет, является ли сообщение агрессивным
        
        Args:
            message_text: Текст сообщения пользователя
            
        Returns:
            True если сообщение агрессивное
        """
        message_lower = message_text.lower()
        
        for pattern in self.aggressive_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True
        
        return False

    def should_respond_harshly(self) -> bool:
        """
        Проверяет, можно ли сейчас дать резкий ответ
        
        Returns:
            True если можно ответить резко
        """
        current_time = time.time()
        time_since_last = current_time - self.last_response_time
        
        return time_since_last >= self.response_cooldown

    def generate_harsh_response(self) -> Optional[str]:
        """
        Генерирует резкий ответ
        
        Returns:
            Сгенерированный резкий ответ или None
        """
        if not self.should_respond_harshly():
            return None
        
        # Выбираем случайный резкий ответ
        import random
        response = random.choice(self.hostile_responses)
        
        # Обновляем время последнего ответа
        self.last_response_time = time.time()
        self._save_last_response_time(self.last_response_time)
        
        return response

    def get_stats(self) -> Dict:
        """Получение статистики резких ответов"""
        current_time = time.time()
        time_since_last = current_time - self.last_response_time
        
        return {
            'last_response_time': self.last_response_time,
            'time_since_last_response': int(time_since_last),
            'can_respond': time_since_last >= self.response_cooldown,
            'next_response_in': max(0, self.response_cooldown - int(time_since_last)),
            'cooldown_minutes': self.response_cooldown // 60
        }


# Глобальный экземпляр менеджера
hostile_response_manager = HostileResponseManager()