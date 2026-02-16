"""
Клиент для работы с API Гигачата
"""
import aiohttp
import json
import uuid
from typing import List, Dict, Optional
from config import GIGACHAT_AUTH_KEY, GIGACHAT_CLIENT_ID, GIGACHAT_SCOPE, SYSTEM_PROMPT, MAX_TOKENS


class GigaChatClient:
    """Клиент для отправки запросов в Гигачат"""

    def __init__(self):
        self.auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        self.api_base_url = "https://gigachat.devices.sberbank.ru/api/v1"
        self.model = "GigaChat"  # Используем базовую модель
        self.auth_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': str(uuid.uuid4()),
            'Authorization': f'Basic {GIGACHAT_AUTH_KEY}'
        }
        self.auth_payload = {
            'scope': GIGACHAT_SCOPE
        }
        self.access_token = None
        self.conversations: Dict[str, List[Dict]] = {}

    def _load_history(self, chat_id: str) -> List[Dict]:
        """Загрузка истории для конкретного чата"""
        return self.conversations.get(chat_id, [])

    def _save_history(self, chat_id: str, messages: List[Dict]):
        """Сохранение истории для конкретного чата"""
        self.conversations[chat_id] = messages

    async def _get_access_token(self) -> bool:
        """
        Получение Access Token через OAuth
        """
        try:
            # Отключаем проверку SSL сертификатов для Гигачата
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    self.auth_url,
                    headers=self.auth_headers,
                    data=self.auth_payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.access_token = data.get('access_token')
                        if self.access_token:
                            return True
                    else:
                        return False
        except Exception as e:
            return False
        return False

    async def chat_with_personalized_prompt(self, user_message: str, chat_id: str, personalized_prompt: str) -> str:
        """
        Отправка сообщения в Гигачат с персонализированным промптом

        Args:
            user_message: Сообщение пользователя
            chat_id: ID беседы/пользователя
            personalized_prompt: Персонализированный промпт для пользователя

        Returns:
            Ответ от Гигачата
        """
        # Проверяем наличие Access Token
        if not self.access_token:
            if not await self._get_access_token():
                return "Мои механизмы сейчас не отвечают... Попробуй позже."

        # Загружаем историю
        messages = self._load_history(chat_id)

        # Если история пустая, добавляем персонализированный системный промпт
        if not messages:
            messages.append({"role": "system", "content": personalized_prompt})
        else:
            # Если есть сообщения, но нет системного промпта, добавляем его
            has_system = any(msg.get("role") == "system" for msg in messages)
            if not has_system:
                messages.insert(0, {"role": "system", "content": personalized_prompt})

        # Добавляем сообщение пользователя
        messages.append({"role": "user", "content": user_message})

        # Заголовки для API запросов
        api_headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }

        try:
            # Отключаем проверку SSL сертификатов для API запросов
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.4,  # Слегка повышена для большей вариативности
                    "max_tokens": MAX_TOKENS
                }

                async with session.post(
                    f"{self.api_base_url}/chat/completions",
                    headers=api_headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        assistant_message = data["choices"][0]["message"]["content"]

                        # Сохраняем сообщение бота в историю
                        messages.append({"role": "assistant", "content": assistant_message})
                        self._save_history(chat_id, messages)

                        return assistant_message
                    else:
                        # Попробуем получить новый токен
                        if response.status == 401:
                            self.access_token = None
                            if await self._get_access_token():
                                return await self.chat_with_personalized_prompt(user_message, chat_id, personalized_prompt)
                        return "Механизмы пока молчат... Попробуй позже."

        except Exception as e:
            return "Что-то сломалось в моих механизмах... Попробуй позже."

    async def chat(self, user_message: str, chat_id: str) -> str:
        """
        Отправка сообщения в Гигачат и получение ответа

        Args:
            user_message: Сообщение пользователя
            chat_id: ID беседы/пользователя

        Returns:
            Ответ от Гигачата
        """
        # Проверяем наличие Access Token
        if not self.access_token:
            if not await self._get_access_token():
                return "Мои механизмы сейчас не отвечают... Попробуй позже."

        # Загружаем историю
        messages = self._load_history(chat_id)

        # Если история пустая, добавляем системный промпт
        if not messages:
            messages.append({"role": "system", "content": SYSTEM_PROMPT})

        # Добавляем сообщение пользователя
        messages.append({"role": "user", "content": user_message})

        # Заголовки для API запросов
        api_headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }

        try:
            # Отключаем проверку SSL сертификатов для API запросов
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.4,  # Слегка повышена для большей вариативности
                    "max_tokens": MAX_TOKENS
                }

                async with session.post(
                    f"{self.api_base_url}/chat/completions",
                    headers=api_headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        assistant_message = data["choices"][0]["message"]["content"]

                        # Сохраняем сообщение бота в историю
                        messages.append({"role": "assistant", "content": assistant_message})
                        self._save_history(chat_id, messages)

                        return assistant_message
                    else:
                        # Попробуем получить новый токен
                        if response.status == 401:
                            self.access_token = None
                            if await self._get_access_token():
                                return await self.chat(user_message, chat_id)
                        return "Механизмы пока молчат... Попробуй позже."

        except Exception as e:
            return "Что-то сломалось в моих механизмах... Попробуй позже."

    async def test_connection(self) -> bool:
        """
        Тестирование подключения к GigaChat API
        """
        if not self.access_token:
            if not await self._get_access_token():
                return False

        api_headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }

        try:
            # Отключаем проверку SSL сертификатов для API запросов
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    f"{self.api_base_url}/models",
                    headers=api_headers
                ) as response:
                    if response.status == 200:
                        print("Подключение к GigaChat API успешно!")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"Ошибка подключения к GigaChat API: {response.status}, {error_text}")
                        return False
        except Exception as e:
            print(f"Ошибка при тестировании подключения: {e}")
            return False

    def clear_history(self, chat_id: str):
        """Очистка истории для конкретного чата"""
        if chat_id in self.conversations:
            del self.conversations[chat_id]


# Глобальный экземпляр клиента
gigachat_client = GigaChatClient()