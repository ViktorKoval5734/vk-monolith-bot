"""
Клиент для работы с API YandexGPT
"""
import aiohttp
import json
import uuid
from typing import List, Dict, Optional
from config import YANDEX_GPT_API_KEY, YANDEX_GPT_FOLDER_ID, YANDEX_GPT_MODEL, SYSTEM_PROMPT, MAX_TOKENS


class YandexGPTClient:
    """Клиент для отправки запросов в YandexGPT"""

    def __init__(self):
        self.api_base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1"
        self.model = YANDEX_GPT_MODEL
        self.conversations: Dict[str, List[Dict]] = {}

    def _load_history(self, chat_id: str) -> List[Dict]:
        """Загрузка истории для конкретного чата"""
        return self.conversations.get(chat_id, [])

    def _save_history(self, chat_id: str, messages: List[Dict]):
        """Сохранение истории для конкретного чата"""
        self.conversations[chat_id] = messages

    async def chat_with_personalized_prompt(self, user_message: str, chat_id: str, personalized_prompt: str) -> str:
        """
        Отправка сообщения в YandexGPT с персонализированным промптом

        Args:
            user_message: Сообщение пользователя
            chat_id: ID беседы/пользователя
            personalized_prompt: Персонализированный промпт для пользователя

        Returns:
            Ответ от YandexGPT
        """
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
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Api-Key {YANDEX_GPT_API_KEY}',
            'x-folder-id': YANDEX_GPT_FOLDER_ID
        }

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "modelUri": f"gpt://{YANDEX_GPT_FOLDER_ID}/{self.model}",
                    "completionOptions": {
                        "stream": False,
                        "temperature": 0.4,
                        "maxTokens": MAX_TOKENS
                    },
                    "messages": messages
                }

                async with session.post(
                    f"{self.api_base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        assistant_message = data["result"]["alternatives"][0]["message"]["text"]

                        # Сохраняем сообщение бота в историю
                        messages.append({"role": "assistant", "content": assistant_message})
                        self._save_history(chat_id, messages)

                        return assistant_message
                    else:
                        error_text = await response.text()
                        return f"Волны Зоны мешают передаче мысли... (ошибка {response.status})"

        except Exception as e:
            return "Сила Монолита временно недоступна... Попробуй позже."

    async def chat(self, user_message: str, chat_id: str) -> str:
        """
        Отправка сообщения в YandexGPT и получение ответа

        Args:
            user_message: Сообщение пользователя
            chat_id: ID беседы/пользователя

        Returns:
            Ответ от YandexGPT
        """
        # Загружаем историю
        messages = self._load_history(chat_id)

        # Если история пустая, добавляем системный промпт
        if not messages:
            messages.append({"role": "system", "content": SYSTEM_PROMPT})

        # Добавляем сообщение пользователя
        messages.append({"role": "user", "content": user_message})

        # Заголовки для API запросов
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Api-Key {YANDEX_GPT_API_KEY}',
            'x-folder-id': YANDEX_GPT_FOLDER_ID
        }

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "modelUri": f"gpt://{YANDEX_GPT_FOLDER_ID}/{self.model}",
                    "completionOptions": {
                        "stream": False,
                        "temperature": 0.4,
                        "maxTokens": MAX_TOKENS
                    },
                    "messages": messages
                }

                async with session.post(
                    f"{self.api_base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        assistant_message = data["result"]["alternatives"][0]["message"]["text"]

                        # Сохраняем сообщение бота в историю
                        messages.append({"role": "assistant", "content": assistant_message})
                        self._save_history(chat_id, messages)

                        return assistant_message
                    else:
                        error_text = await response.text()
                        return f"Волны Зоны мешают передаче мысли... (ошибка {response.status})"

        except Exception as e:
            return "Сила Монолита временно недоступна... Попробуй позже."

    async def test_connection(self) -> bool:
        """
        Тестирование подключения к YandexGPT API
        """
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Api-Key {YANDEX_GPT_API_KEY}',
            'x-folder-id': YANDEX_GPT_FOLDER_ID
        }

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "modelUri": f"gpt://{YANDEX_GPT_FOLDER_ID}/{self.model}",
                    "completionOptions": {
                        "stream": False,
                        "temperature": 0.4,
                        "maxTokens": 10
                    },
                    "messages": [{"role": "user", "content": "Привет"}]
                }

                async with session.post(
                    f"{self.api_base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        print("Подключение к YandexGPT API успешно!")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"Ошибка подключения к YandexGPT API: {response.status}, {error_text}")
                        return False
        except Exception as e:
            print(f"Ошибка при тестировании подключения: {e}")
            return False

    def clear_history(self, chat_id: str):
        """Очистка истории для конкретного чата"""
        if chat_id in self.conversations:
            del self.conversations[chat_id]


# Глобальный экземпляр клиента
yandex_gpt_client = YandexGPTClient()
