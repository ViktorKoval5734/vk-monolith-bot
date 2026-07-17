"""
Модуль для работы с базой знаний по STALKER Anomaly
"""
import json
import os
from typing import Dict, List, Optional
from config import KNOWLEDGE_BASE_FILE


class KnowledgeBase:
    """База знаний по частым проблемам STALKER Anomaly"""

    def __init__(self):
        self.file_path = KNOWLEDGE_BASE_FILE
        self.knowledge = {}
        self._load()

    def _load(self):
        """Загрузка базы знаний из файла"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.knowledge = json.load(f)
                print(f"База знаний загружена: {len(self.knowledge)} записей")
            except Exception as e:
                print(f"Ошибка загрузки базы знаний: {e}")
                self.knowledge = {}
        else:
            print("Файл базы знаний не найден, будет создана пустая база")
            self.knowledge = {}

    def _save(self):
        """Сохранение базы знаний в файл"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения базы знаний: {e}")

    def search(self, query: str, threshold: float = 0.3) -> Optional[Dict]:
        """
        Поиск ответа в базе знаний

        Args:
            query: Запрос пользователя
            threshold: Порог сходства (0-1)

        Returns:
            Найденная запись или None
        """
        if not self.knowledge:
            return None

        query_lower = query.lower()
        best_match = None
        best_score = 0

        for entry in self.knowledge.get('entries', []):
            # Проверяем ключевые слова
            keywords = entry.get('keywords', [])
            keyword_match = False

            for keyword in keywords:
                if keyword.lower() in query_lower:
                    keyword_match = True
                    break

            # Проверяем заголовок
            title = entry.get('title', '').lower()
            title_score = self._calculate_similarity(query_lower, title)

            # Проверяем вопрос/проблему
            problem = entry.get('problem', '').lower()
            problem_score = self._calculate_similarity(query_lower, problem)

            # Итоговая оценка
            if keyword_match:
                score = max(title_score, problem_score) + 0.5
            else:
                score = max(title_score, problem_score)

            if score > best_score:
                best_score = score
                best_match = entry

        if best_score >= threshold:
            return best_match
        return None

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Простая оценка сходства текстов

        Args:
            text1: Первый текст
            text2: Второй текст

        Returns:
            Оценка сходства (0-1)
        """
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0

    def add_entry(self, title: str, problem: str, solution: str, keywords: List[str], category: str = "general"):
        """
        Добавление записи в базу знаний

        Args:
            title: Заголовок
            problem: Описание проблемы
            solution: Решение
            keywords: Ключевые слова для поиска
            category: Категория
        """
        if 'entries' not in self.knowledge:
            self.knowledge['entries'] = []

        entry = {
            'title': title,
            'problem': problem,
            'solution': solution,
            'keywords': keywords,
            'category': category,
            'created_at': None  # Можно добавить timestamp
        }

        self.knowledge['entries'].append(entry)
        self._save()
        print(f"Добавлена запись: {title}")

    def get_all_entries(self) -> List[Dict]:
        """Получить все записи базы знаний"""
        return self.knowledge.get('entries', [])

    def get_by_category(self, category: str) -> List[Dict]:
        """Получить записи по категории"""
        return [
            entry for entry in self.knowledge.get('entries', [])
            if entry.get('category') == category
        ]


# Глобальный экземпляр базы знаний
knowledge_base = KnowledgeBase()
