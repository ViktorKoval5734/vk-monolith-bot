"""
Проверка дней рождения участников бесед
Запускается ежедневно в 9:00 по МСК
"""
import logging
import aiohttp
from datetime import datetime, timezone, timedelta
from config import VK_TOKEN, VK_API_URL, VK_API_VERSION

logger = logging.getLogger(__name__)

# МСК = UTC+3
MSK_TZ = timezone(timedelta(hours=3))

# Поздравления
BIRTHDAY_TEMPLATE = "Сегодня в Зоне празднуют День Рождения! Сталкеры, поздравьте же братьев, что очередной год делят с вами консервы и патроны! {mentions}, с праздником!!!"


async def _get_conversations() -> list:
    """Получить список бесед, в которых состоит группа"""
    params = {
        "access_token": VK_TOKEN,
        "v": VK_API_VERSION,
        "fields": "members.id"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{VK_API_URL}groups.getConversations",
            params=params
        ) as response:
            data = await response.json()
            if "response" in data:
                return data["response"].get("items", [])
    return []


async def _get_members(peer_id: int) -> list:
    """Получить список участников беседы"""
    params = {
        "peer_id": peer_id,
        "access_token": VK_TOKEN,
        "v": VK_API_VERSION,
        "fields": "bdate"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{VK_API_URL}messages.getConversationMembers",
            params=params
        ) as response:
            data = await response.json()
            if "response" in data:
                members = data["response"].get("members", [])
                return [m["user"] for m in members]
    return []


async def _get_users_info(user_ids: list) -> list:
    """Получить информацию о пользователях (имена + даты рождения)"""
    params = {
        "user_ids": ",".join(str(uid) for uid in user_ids),
        "access_token": VK_TOKEN,
        "v": VK_API_VERSION,
        "fields": "bdate,first_name"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{VK_API_URL}users.get",
            params=params
        ) as response:
            data = await response.json()
            if "response" in data:
                return data["response"]
    return []


async def _send_message(peer_id: int, message: str) -> bool:
    """Отправить сообщение в беседу"""
    params = {
        "peer_id": peer_id,
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
                logger.error(f"Ошибка отправки поздравления: {data['error']}")
                return False
            logger.info(f"✅ Поздравление отправлено в peer_id={peer_id}")
            return True


def _parse_bdate(bdate: str) -> tuple:
    """
    Парсит дату рождения в формате DD.MM.YYYY или DD.MM
    Возвращает (день, месяц) или None
    """
    if not bdate:
        return None
    parts = bdate.split(".")
    if len(parts) == 3:
        return int(parts[0]), int(parts[1])
    elif len(parts) == 2:
        return int(parts[0]), int(parts[1])
    return None


async def check_birthdays():
    """Основная функция проверки дней рождения"""
    now = datetime.now(MSK_TZ)
    today_day = now.day
    today_month = now.month

    logger.info(f"🎂 Проверка дней рождения на {today_day}.{today_month:02d}...")

    # Получаем все беседы
    conversations = await _get_conversations()
    logger.info(f"📋 Найдено {len(conversations)} бесед")

    for conv in conversations:
        peer_id = conv.get("peer_id")
        if not peer_id:
            continue

        # Получаем участников беседы
        members = await _get_members(peer_id)
        if not members:
            continue

        # Фильтруем тех, у кого есть bdate
        users_with_bdate = [m for m in members if m.get("bdate")]
        if not users_with_bdate:
            continue

        # Получаем полные данные о пользователях с bdate
        user_ids = [m["id"] for m in users_with_bdate]
        users_info = await _get_users_info(user_ids)

        # Ищем именинников
        birthday_people = []
        for user in users_info:
            bdate = user.get("bdate")
            if not bdate:
                continue
            parsed = _parse_bdate(bdate)
            if parsed:
                day, month = parsed
                if day == today_day and month == today_month:
                    birthday_people.append({
                        "id": user["id"],
                        "name": user.get("first_name", "Сталкер")
                    })

        if birthday_people:
            # Формируем упоминания
            mentions = ", ".join(
                f"@id{p['id']}" for p in birthday_people
            )
            message = BIRTHDAY_TEMPLATE.format(mentions=mentions)
            await _send_message(peer_id, message)
            logger.info(f"🎉 Именинники в peer_id={peer_id}: {len(birthday_people)} чел.")
        else:
            logger.info(f"🔍 В peer_id={peer_id} именинников нет")
