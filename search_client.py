"""
Клиент для поиска актуальной информации через Serper API
"""
import aiohttp
import json
from typing import List, Dict, Optional
from config import SERPER_API_KEY


class SearchClient:
    """Клиент для поиска через Serper API"""

    def __init__(self):
        self.api_url = "https://google.serper.dev/search"
        self.api_key = SERPER_API_KEY

    async def search(self, query: str, num_results: int = 5) -> Optional[List[Dict]]:
        """
        Выполнение поиска через Serper API

        Args:
            query: Поисковый запрос
            num_results: Количество результатов для возврата

        Returns:
            Список результатов поиска или None при ошибке
        """
        if not self.api_key:
            return None

        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        }

        payload = {
            'q': query,
            'num': num_results
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []

                        # Обрабатываем органические результаты
                        if 'organic' in data:
                            for item in data['organic'][:num_results]:
                                results.append({
                                    'title': item.get('title', ''),
                                    'snippet': item.get('snippet', ''),
                                    'link': item.get('link', ''),
                                    'snippetHighlighted': item.get('snippetHighlighted', [])
                                })

                        # Добавляем ответ из featured snippet если есть
                        if 'answerBox' in data:
                            answer = data['answerBox']
                            results.insert(0, {
                                'title': 'Ответ из поиска',
                                'snippet': answer.get('answer', '') or answer.get('snippet', ''),
                                'link': answer.get('link', ''),
                                'is_featured': True
                            })

                        return results if results else None
                    else:
                        error_text = await response.text()
                        print(f"Ошибка поиска: {response.status}")
                        print(f"Заголовки запроса: {headers}")
                        print(f"Ответ: {error_text}")
                        return None

        except Exception as e:
            print(f"Ошибка при поиске: {e}")
            return None


    def format_results(self, search_data: List[Dict]) -> str:
        """
        Форматирование результатов поиска в читаемый вид

        Args:
            search_data: Список результатов поиска от Serper API

        Returns:
            Отформатированный текст с результатами (сниппет|||ссылка)
        """
        if not search_data or not isinstance(search_data, list):
            return "Монолит не может проникнуть в тайны внешнего мира..."

        # Берём только первый результат (наиболее релевантный)
        result = search_data[0]
        snippet = result.get("snippet", "Нет описания")
        link = result.get("link", "")

        # Возвращаем только сниппет и ссылку (без форматирования)
        return f"{snippet}|||{link}"

    async def search_with_context(self, query: str, context: str = "") -> Optional[str]:
        """
        Поиск с контекстом для техподдержки STALKER Anomaly

        Args:
            query: Основной запрос
            context: Дополнительный контекст (например, "STALKER Anomaly моды")

        Returns:
            Сформированный контекст из результатов поиска или None
        """
        full_query = f"{query} {context}".strip()
        results = await self.search(full_query, num_results=5)

        if not results:
            return None

        # Формируем контекст из результатов
        context_parts = []
        for i, result in enumerate(results, 1):
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            link = result.get('link', '')

            if title and snippet:
                context_parts.append(f"[{i}] {title}\n{snippet}\nИсточник: {link}")

        return "\n\n".join(context_parts) if context_parts else None

    async def test_connection(self) -> bool:
        """
        Тестирование подключения к Serper API
        """
        if not self.api_key:
            print("Serper API ключ не настроен")
            return False

        try:
            result = await self.search("test query", num_results=1)
            if result is not None:
                print("Подключение к Serper API успешно!")
                return True
            else:
                print("Ошибка подключения к Serper API")
                return False
        except Exception as e:
            print(f"Ошибка при тестировании подключения: {e}")
            return False


# Глобальный экземпляр клиента
search_client = SearchClient()
