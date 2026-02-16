"""
Бот "Монолит" для ВКонтакте
Основной файл с веб-сервером и обработкой сообщений
"""
import asyncio
import json
import hashlib
import hmac
import logging
import re
import time
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import VK_TOKEN, VK_GROUP_ID, VK_API_URL, VK_API_VERSION, CONFIRMATION_SECRET, SYSTEM_PROMPT
from gigachat_client import gigachat_client
from search_client import search_client
from knowledge_base import knowledge_base
from history import history_manager
from user_preferences import user_preferences
from confirmation_manager import confirmation_manager
from message_deduplicator import message_deduplicator
from hostile_responses import hostile_response_manager
from random_comments import random_comments_manager



def extract_search_query(text: str) -> str:
    """
    Извлечение поискового запроса из текста
    
    Args:
        text: Текст сообщения
        
    Returns:
        Очищенный поисковый запрос
    """
    # Удаляем типичные слова-паразиты
    stop_words = ['что', 'как', 'почему', 'зачем', 'когда', 'где', 'кто', 
                  'какой', 'какая', 'какое', 'какие', 'каким', 'какими',
                  'скажи', 'расскажи', 'объясни', 'покажи', 'найди',
                  'узнай', 'поясни', 'подскажи']
    
    query = text.lower()
    for word in stop_words:
        query = query.replace(word, '')
    
    # Удаляем лишние пробелы и знаки препинания
    query = re.sub(r'[?!.,;:]+', ' ', query)
    query = ' '.join(query.split())
    
    return query.capitalize() if query else text

def safe_log_message(message: str, max_length: int = 100) -> str:
    """Безопасное логирование сообщений (обрезка длинных URL и текстов)"""
    if len(message) > max_length:
        return message[:max_length] + "..."
    return message

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Отключаем verbose логи от HTTP библиотек
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)
logging.getLogger("fastapi").setLevel(logging.WARNING)

app = FastAPI(title="Монолит - VK Bot")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def send_message(user_id: int, peer_id: int = None, message: str = None) -> bool:
    """
    Отправка сообщения через VK API

    Args:
        user_id: ID пользователя (отправитель)
        peer_id: ID получателя (пользователь или беседа)
        message: Текст сообщения

    Returns:
        True если отправлено успешно
    """
    import aiohttp

    # Определяем получателя
    if peer_id:
        # Отправка в беседу
        recipient_id = peer_id
        logger.info(f"📤 Отправка в беседу {peer_id}")
    else:
        # Отправка личного сообщения
        recipient_id = user_id
        logger.info(f"📤 Отправка личного сообщения пользователю {user_id}")

    params = {
        "peer_id": recipient_id,
        "message": message,
        "access_token": VK_TOKEN,
        "v": VK_API_VERSION,
        "random_id": 0
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{VK_API_URL}messages.send",
            params=params
        ) as response:
            data = await response.json()
            if "error" in data:
                logger.error(f"Ошибка отправки: {data['error']}")
                return False
            logger.info(f"✅ Сообщение отправлено получателю {recipient_id}")
            return True


async def get_user_name(user_id: int) -> str:
    """
    Получение имени пользователя ВКонтакте

    Args:
        user_id: ID пользователя

    Returns:
        Имя пользователя или "Друг"
    """
    import aiohttp

    params = {
        "user_ids": user_id,
        "access_token": VK_TOKEN,
        "v": VK_API_VERSION,
        "fields": "first_name"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{VK_API_URL}users.get",
            params=params
        ) as response:
            data = await response.json()
            if "response" in data:
                user = data["response"][0]
                return user.get("first_name", "Друг")
    return "Друг"


def check_secret_secret_type(event: Dict) -> bool:
    """
    Проверка секретного ключа Callback API

    Args:
        event: Событие от ВКонтакте

    Returns:
        True если ключ валиден
    """
    # Если секрет не настроен, пропускаем проверку
    if not CONFIRMATION_SECRET or CONFIRMATION_SECRET == "your_confirmation_secret":
        return True

    if "secret" not in event:
        return False

    return hmac.new(
        CONFIRMATION_SECRET.encode(),
        json.dumps(event).encode(),
        hashlib.sha256
    ).hexdigest() == event["secret"]


@app.get("/update_confirmation/{new_code}")
async def update_confirmation_code(new_code: str):
    """Обновление кода подтверждения через GET запрос"""
    confirmation_manager.save_code(new_code)
    logger.info(f"🔄 Код подтверждения обновлён: {new_code}")
    return {"status": "updated", "code": new_code}

@app.get("/confirmation_status")
async def confirmation_status():
    """Получение статуса кода подтверждения"""
    status = confirmation_manager.get_status()
    return {
        "status": status,
        "instructions": confirmation_manager.get_setup_instructions()
    }

@app.get("/deduplicator_status")
async def deduplicator_status():
    """Получение статуса дедупликатора сообщений"""
    stats = message_deduplicator.get_stats()
    return {
        "deduplicator_stats": stats,
        "description": "Статистика системы предотвращения дублирования сообщений"
    }

@app.get("/hostile_responses_status")
async def hostile_responses_status():
    """Получение статуса системы резких ответов"""
    stats = hostile_response_manager.get_stats()
    return {
        "hostile_responses_stats": stats,
        "description": "Статистика системы резких ответов на негативные сообщения"
    }

@app.get("/random_comments_status")
async def random_comments_status():
    """Получение статуса системы случайных комментариев"""
    stats = random_comments_manager.get_stats()
    return {
        "random_comments_stats": stats,
        "description": "Статистика системы случайных комментариев без упоминаний"
    }

@app.post("/")
async def vk_callback(request: Request):
    """
    Обработка событий от ВКонтакте (Callback API)
    """
    try:
        event = await request.json()
        logger.info(f"Получено событие: {event.get('type', 'unknown')}")
        event_type = event.get("type")

        # Обработка подтверждения
        if event_type == "confirmation":
            # Сначала пробуем загрузить код из переменной окружения
            confirmation_manager.update_code_from_env()
            
            # Получаем код подтверждения
            confirmation_code = confirmation_manager.get_code()
            
            if confirmation_code:
                logger.info(f"✅ Используется код подтверждения: {confirmation_code}")
                return PlainTextResponse(content=confirmation_code)
            else:
                # Код не найден - логируем и возвращаем стандартный ответ
                logger.error("❌ Код подтверждения не настроен!")
                logger.info("📋 Инструкции по настройке:")
                logger.info(confirmation_manager.get_setup_instructions())
                return PlainTextResponse(content="ok")

        # Проверка секрета (временно отключена для тестирования)
        # if not check_secret_secret_type(event):
        #     raise HTTPException(status_code=403, detail="Invalid secret")

        # Обработка новых сообщений
        if event_type == "message_new":
            await handle_message(event["object"]["message"])

        return {"response": "ok"}

    except Exception as e:
        logger.error(f"Ошибка обработки события: {e}")
        return {"response": "ok"}


async def handle_message(message: Dict):
    """
    Обработка входящего сообщения

    Args:
        message: Данные сообщения
    """
    # Получаем ID сообщения для дедупликации
    message_id = message.get("id")
    text = message.get("text", "").strip()
    user_id = message.get("from_id")
    message_date = message.get("date", 0)
    peer_id = message.get("peer_id")
    
    # Проверяем на дубликат
    is_duplicate, reason = message_deduplicator.is_duplicate(
        message_id=message_id,
        text=text,
        user_id=user_id,
        peer_id=peer_id
    )
    
    if is_duplicate:
        logger.info(f"⏭️ Дубликат: {reason}")
        return
    
    if not text or not user_id:
        return
    
    # Проверяем время сообщения (не старше 1 минуты)
    current_time = int(time.time())
    if current_time - message_date > 60:  # 60 секунд = 1 минута
        logger.info(f"⏰ Старое сообщение ({current_time - message_date}s), пропускаем")
        return

    # Проверяем тип сообщения
    is_conversation = "peer_id" in message and message.get("peer_id", 0) > 2000000000
    
    if not is_conversation:
        # Личное сообщение - НЕ отвечаем
        logger.info(f"👤 Личное сообщение - пропускаем")
        return
    
    # Это сообщение из беседы
    logger.info(f"💬 Сообщение из беседы: {message.get('peer_id')}")
    
    # Очищаем текст от формата упоминания ВКонтакте (делаем сразу, чтобы использовать везде)
    clean_text = text
    for pattern in [f"[club{VK_GROUP_ID}|", "]"]:
        clean_text = clean_text.replace(pattern, "")
    
    # Проверяем упоминания
    is_mention = False
    
    # Проверяем разные форматы упоминания
    mention_patterns = [
        f"[club{VK_GROUP_ID}|",
        f"@club{VK_GROUP_ID}",
        "Монолит",
        "творец зоны",
        "Исполнитель Желаний",
        "Исполнитель",
        "хранитель зоны",
        "дух зоны",
        "камушек",
        "камень",
        "монолит",
        "монолита"
    ]
    
    for pattern in mention_patterns:
        if pattern.lower() in text.lower():
            is_mention = True
            logger.info(f"✅ Найдено упоминание: {pattern}")
            break

    # Проверяем, является ли сообщение ответом на сообщение бота
    if not is_mention:
        # Проверяем reply_message (ответ на конкретное сообщение)
        if "reply_message" in message:
            reply_msg = message["reply_message"]
            if reply_msg.get("from_id") == -int(VK_GROUP_ID):  # Группы имеют отрицательный ID
                is_mention = True
                logger.info(f"✅ Найден ответ на сообщение бота")
        
        # Проверяем fwd_messages (пересланные сообщения)
        if not is_mention and "fwd_messages" in message:
            for fwd_msg in message.get("fwd_messages", []):
                if fwd_msg.get("from_id") == -int(VK_GROUP_ID):
                    is_mention = True
                    logger.info(f"✅ Найдено пересланное сообщение от бота")
                    break

    # Если упоминание не найдено, проверяем на случайные комментарии
    if not is_mention:
        logger.info(f"⏭️ Сообщение без упоминания в беседе, проверяем случайные комментарии...")
        
        # Проверяем, стоит ли оставить случайный комментарий
        if random_comments_manager.should_comment(clean_text):
            logger.info(f"💬 Генерируем случайный комментарий для сообщения: {clean_text[:50]}...")
            random_comment = random_comments_manager.generate_comment(clean_text)
            
            if random_comment:
                logger.info(f"🎲 Случайный комментарий: {random_comment}")
                # Отправляем случайный комментарий в беседу
                await send_message(user_id, message.get("peer_id"), random_comment)
                return
        
        # Если нет случайного комментария, полностью пропускаем сообщение
        logger.info(f"⏭️ Сообщение без упоминания, случайный комментарий не требуется")
        return

    # Получаем имя пользователя
    user_name = await get_user_name(user_id)

    logger.info(f"📝 Сообщение от {user_name}: {clean_text}")

    # Проверяем команды настройки (только при упоминании)
    setup_response = user_preferences.parse_setup_command(user_id, clean_text)
    if setup_response:
        logger.info(f"🔧 Выполнена команда настройки: {setup_response}")
        # Отправляем ответ на команду настройки
        await send_message(user_id, message.get("peer_id"), setup_response)
        return
    
    # Проверяем команду показа списка настроек (только при упоминании)
    if "настройки" in clean_text.lower() and ("команды" in clean_text.lower() or "что" in clean_text.lower()):
        commands_list = user_preferences.list_user_commands()
        logger.info(f"🔧 Показан список команд настройки")
        # Отправляем список команд
        await send_message(user_id, message.get("peer_id"), commands_list)
        return

    # Проверяем на агрессивные сообщения
    if hostile_response_manager.is_aggressive_message(clean_text):
        logger.info(f"⚠️ Обнаружено агрессивное сообщение от {user_name}")
        harsh_response = hostile_response_manager.generate_harsh_response()
        if harsh_response:
            logger.info(f"💢 Ответ с агрессией: {harsh_response[:50]}...")
            await send_message(user_id, message.get("peer_id"), harsh_response)
            return
        else:
            logger.info(f"⏰ Агрессивный ответ отклонён (кулдаун)")
            # Можно отправить нейтральный ответ или пропустить

    # Определяем ID чата для истории (только для бесед)
    chat_id = str(message.get("peer_id"))

    # Слова-триггеры для поиска в интернете
    search_trigger_words = [
        "найди", "поищи", "загугли", "погугли", "узнай",
        "сколько", "как называется", "кто такой", "что такое", "где находится",
        "как сделать"
    ]

    # Проверяем, есть ли триггер поиска в сообщении
    has_search_trigger = any(word.lower() in clean_text.lower() for word in search_trigger_words)

    # Проверяем базу знаний и выполняем поиск
    kb_entry = knowledge_base.search(clean_text, threshold=0.3)
    search_context = None
    response = ""

    # Определяем, нужно ли выполнять поиск
    should_search = kb_entry is not None or has_search_trigger

    if should_search:
        # Если найдено в базе знаний, используем её решение
        if kb_entry:
            logger.info(f"📚 Найдено в базе знаний: {kb_entry.get('title', '')}")
            response = kb_entry.get('solution', '')
            logger.info(f"📦 Ответ из базы знаний: {response[:100]}...")
        else:
            logger.info(f"🔍 Триггер поиска найден: {[w for w in search_trigger_words if w.lower() in clean_text.lower()][0]}")

        # Ищем в интернете
        logger.info(f"🔍 Выполняем поиск в интернете...")
        search_query = extract_search_query(clean_text)
        logger.info(f"🔍 Поисковый запрос: {search_query}")

        # Выполняем поиск через Serper
        search_data = await search_client.search(search_query)

        if search_data:
            # Форматируем результаты (получаем сниппет и ссылку)
            formatted_results = search_client.format_results(search_data)

            # Разделяем сниппет и ссылку
            if "|||" in formatted_results:
                snippet, link = formatted_results.split("|||", 1)

                if kb_entry:
                    # Если был ответ из базы знаний - дополняем его
                    search_prompt = f"""Вот краткая информация из внешнего мира по запросу "{search_query}":

{snippet}

Твоя задача: дополнить этот ответ, сохранив его суть и содержание. НЕ меняй основной смысл и факты. Можно добавить детали, пояснения или контекст, но основная информация должна остаться неизменной. Отвечай как Монолит — таинственно, пророчески, используя термины Зоны. Не добавляй лишних вступлений. Кратко и по сути."""

                    response = await gigachat_client.chat_with_personalized_prompt(
                        search_prompt, chat_id, SYSTEM_PROMPT
                    )
                else:
                    # Если НЕ было ответа из базы знаний - генерируем полный ответ
                    search_prompt = f"""Пользователь спрашивает: "{clean_text}"

Вот информация из внешнего мира по этому запросу:

{snippet}

Твоя задача: ответить на вопрос пользователя, используя эту информацию. Дай полный, развёрнутый ответ. Отвечай как Монолит — таинственно, пророчески, используя термины Зоны. Не добавляй лишних вступлений."""

                    response = await gigachat_client.chat_with_personalized_prompt(
                        search_prompt, chat_id, SYSTEM_PROMPT
                    )

                response = f"{response}\n\nИсточник: {link}"
                logger.info(f"✅ Поиск выполнен успешно, ответ дополнен Гигачатом")
            else:
                # Если формат неверный, возвращаем как есть
                response = "Монолит не может проникнуть в тайны внешнего мира..."
                logger.info(f"❌ Неверный формат результатов поиска")
        else:
            response = "Монолит не может проникнуть в тайны внешнего мира... Возможно, механизмы поиска временно недоступны."
            logger.info(f"❌ Поиск не удался")

        # Сохраняем сообщение пользователя в историю
        history_manager.add_message(chat_id, "user", clean_text)

        # Для Любови добавляем обращение в начало ответа, если его там нет
        special_name = user_preferences.get_special_name(user_id)
        if special_name == "Любовь":
            # Проверяем, есть ли уже обращение "моя королева" в тексте
            if "моя королева" not in response.lower():
                response = f"Моя королева, {response}"
                logger.info(f"👑 Добавлено обращение для Любови")
            else:
                logger.info(f"👑 Обращение уже присутствует в ответе")

        # Для Титомира добавляем обращение в начало ответа, если его там нет
        if special_name == "Титомир":
            # Проверяем, есть ли уже обращение "неопытный менестрель" в тексте
            if "неопытный менестрель" not in response.lower():
                response = f"Неопытный менестрель, {response}"
                logger.info(f"🎭 Добавлено обращение для Титомира")
            else:
                logger.info(f"🎭 Обращение уже присутствует в ответе")
    else:
        # Если нет триггера поиска и нет совпадения в базе знаний - обычный ответ через Гигачат
        logger.info(f"🤖 Обычный запрос - генерация ответа через Гигачат")
        response = await gigachat_client.chat(clean_text, chat_id)

        # Сохраняем сообщение пользователя в историю
        history_manager.add_message(chat_id, "user", clean_text)

        # Для Любови добавляем обращение в начало ответа, если его там нет
        special_name = user_preferences.get_special_name(user_id)
        if special_name == "Любовь":
            # Проверяем, есть ли уже обращение "моя королева" в тексте
            if "моя королева" not in response.lower():
                response = f"Моя королева, {response}"
                logger.info(f"👑 Добавлено обращение для Любови")
            else:
                logger.info(f"👑 Обращение уже присутствует в ответе")

        # Для Титомира добавляем обращение в начало ответа, если его там нет
        if special_name == "Титомир":
            # Проверяем, есть ли уже обращение "неопытный менестрель" в тексте
            if "неопытный менестрель" not in response.lower():
                response = f"Неопытный менестрель, {response}"
                logger.info(f"🎭 Добавлено обращение для Титомира")
            else:
                logger.info(f"🎭 Обращение уже присутствует в ответе")

    # Сохраняем ответ в историю
    history_manager.add_message(chat_id, "assistant", response)

    # Отправляем ответ в беседу
    await send_message(user_id, message.get("peer_id"), response)


async def main():
    """Запуск бота"""
    import aiohttp

    logger.info("🚀 Запуск бота 'Монолит'...")

    # Проверка подключения к VK API
    logger.info("📡 Проверка подключения к ВКонтакте...")
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{VK_API_URL}groups.getById",
            params={
                "group_ids": VK_GROUP_ID,
                "access_token": VK_TOKEN,
                "v": VK_API_VERSION
            }
        ) as response:
            data = await response.json()
            if "response" in data and "groups" in data["response"] and data["response"]["groups"]:
                group = data["response"]["groups"][0]
                logger.info(f"✅ Подключение к ВКонтакте: '{group.get('name', 'Монолит')}'")
            else:
                logger.error(f"❌ Ошибка подключения к VK")
                return

    # Проверка подключения к Гигачату
    logger.info("🤖 Проверка подключения к Гигачату...")
    if await gigachat_client.test_connection():
        logger.info("✅ Подключение к Гигачату: успешно!")
    else:
        logger.error("❌ Ошибка подключения к Гигачату")
        return

    # Проверка подключения к Serper API
    logger.info("🔍 Проверка подключения к Serper API...")
    if await search_client.test_connection():
        logger.info("✅ Подключение к Serper: успешно!")
    else:
        logger.warning("⚠️ Serper API недоступен, поиск в интернете не будет работать")

    # Запуск веб-сервера
    import os
    port = int(os.environ.get('PORT', 8000))
    
    logger.info(f"🌐 Запуск веб-сервера на порту {port}...")
    logger.info("📝 Для настройки Callback API в ВКонтакте используйте URL: http://localhost:8000")
    logger.info("💡 Для локального тестирования запустите: ngrok http 8000")
    config = uvicorn.Config(app, host="0.0.0.0", port=port)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get('PORT', 8000))
    
    if os.environ.get('RENDER'):
        # Для Render.com
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        # Для локального запуска
        asyncio.run(main())
