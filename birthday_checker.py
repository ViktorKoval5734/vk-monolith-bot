"""
Проверка дней рождения участников бесед
Запускается ежедневно в 9:00 по МСК
"""
import logging
import aiohttp
import re
from datetime import datetime, timezone, timedelta
from config import VK_TOKEN, VK_API_URL, VK_API_VERSION, VK_GROUP_ID

logger = logging.getLogger(__name__)

# МСК = UTC+3
MSK_TZ = timezone(timedelta(hours=3))

# Поздравления
BIRTHDAY_TEMPLATE = "Сегодня в Зоне празднуют День Рождения! Сталкеры, поздравьте же братьев, что очередной год делят с вами консервы и патроны! {mentions}, с праздником!!!"


async def _get_group_chat_peer_id() -> int:
    """Получить peer_id группового чата сообщества"""
    params = {
        "access_token": VK_TOKEN,
        "v": VK_API_VERSION,
        "group_id": VK_GROUP_ID,
        "filter": "groups",
        "count": 50,
        "offset": 0
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{VK_API_URL}messages.getConversations",
            params=params
        ) as response:
            data = await response.json()
            if "error" in data:
                logger.error(f"Ошибка получения бесед: {data['error']}")
                return None
            if "response" in data and "items" in data["response"]:
                items = data["response"]["items"]
                if items:
                    peer_id = items[0].get("peer", {}).get("id")
                    logger.info(f"📋 Найдено {len(items)} бесед, берём peer_id={peer_id}")
                    return peer_id
    return None


async def _get_group_members() -> list:
    """Получить список всех участников группы с датами рождения"""
    all_members = []
    offset = 0
    count = 1000

    while True:
        params = {
            "access_token": VK_TOKEN,
            "v": VK_API_VERSION,
            "group_id": VK_GROUP_ID,
            "fields": "bdate",
            "offset": offset,
            "count": count
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{VK_API_URL}groups.getMembers",
                params=params
            ) as response:
                data = await response.json()
                if "error" in data:
                    logger.error(f"Ошибка получения участников: {data['error']}")
                    break
                if "response" in data:
                    response_data = data["response"]
                    if isinstance(response_data, dict):
                        members = response_data.get("items", [])
                        total = response_data.get("count", len(members))
                    else:
                        members = response_data
                        total = len(members)

                    all_members.extend(members)
                    logger.info(f"👥 Получено {len(all_members)} участников (из {total})")

                    if len(all_members) >= total:
                        break
                    offset += count
                else:
                    break

    return all_members


async def _get_users_info(user_ids: list) -> list:
    """Получить имена пользователей по ID"""
    params = {
        "user_ids": ",".join(str(uid) for uid in user_ids),
        "access_token": VK_TOKEN,
        "v": VK_API_VERSION,
        "fields": "first_name,last_name"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{VK_API_URL}users.get",
            params=params
        ) as response:
            data = await response.json()
            if "error" in data:
                logger.error(f"Ошибка получения пользователей: {data['error']}")
                return []
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
    """Парсит дату рождения в формате DD.MM.YYYY или DD.MM"""
    if not bdate:
        return None
    parts = bdate.split(".")
    if len(parts) == 3:
        return int(parts[0]), int(parts[1])
    elif len(parts) == 2:
        return int(parts[0]), int(parts[1])
    return None


async def get_todays_birthdays_message() -> str:
    """
    Получить текст поздравления с днями рождения на сегодня.
    Возвращает текст поздравления или сообщение об отсутствии именинников.
    """
    now = datetime.now(MSK_TZ)
    today_day = now.day
    today_month = now.month

    logger.info(f"🎂 Ручная проверка дней рождения на {today_day}.{today_month:02d}...")

    # Получаем участников группы
    members = await _get_group_members()
    if not members:
        return "Монолит не смог получить список участников Зоны..."

    # Фильтруем тех, у кого есть bdate
    users_with_bdate = [m for m in members if m.get("bdate")]
    logger.info(f"👥 Всего участников: {len(members)}, с датами рождения: {len(users_with_bdate)}")

    if not users_with_bdate:
        return "Монолит не обнаружил в Зоне сталкеров с известными датами рождения."

    # Получаем полные имена для пользователей с bdate
    user_ids = [m["id"] for m in users_with_bdate]
    users_info = await _get_users_info(user_ids)

    # Ищем именинников
    birthday_people = []
    for user in users_info:
        user_id = user.get("id")
        member = next((m for m in users_with_bdate if m["id"] == user_id), None)
        if not member:
            continue

        bdate = member.get("bdate")
        if not bdate:
            continue

        parsed = _parse_bdate(bdate)
        if parsed:
            day, month = parsed
            if day == today_day and month == today_month:
                first_name = user.get("first_name", "")
                last_name = user.get("last_name", "")
                name = f"{first_name} {last_name}".strip() or "Сталкер"
                birthday_people.append({
                    "id": user_id,
                    "name": name
                })

    if birthday_people:
        mentions = ", ".join(
            f"@id{p['id']} ({p['name']})" for p in birthday_people
        )
        message = BIRTHDAY_TEMPLATE.format(mentions=mentions)
        logger.info(f"🎉 Именинников найдено: {len(birthday_people)} чел.")
        for p in birthday_people:
            logger.info(f"   🎂 {p['name']} (@id{p['id']})")
        return message
    else:
        return "Сегодня в Зоне никто не празднует День Рождения. Монолит не зафиксировал никаких праздничных аномалий."


async def check_birthdays():
    """Основная функция проверки дней рождения (ежедневная)"""
    now = datetime.now(MSK_TZ)
    today_day = now.day
    today_month = now.month

    logger.info(f"🎂 Ежедневная проверка дней рождения на {today_day}.{today_month:02d}...")

    # Получаем peer_id группового чата
    peer_id = await _get_group_chat_peer_id()
    if not peer_id:
        logger.warning("⚠️ Не удалось найти групповой чат. Проверьте, что бот состоит в беседе.")
        return

    # Получаем участников группы
    members = await _get_group_members()
    if not members:
        logger.warning("⚠️ Не удалось получить участников группы")
        return

    # Фильтруем тех, у кого есть bdate
    users_with_bdate = [m for m in members if m.get("bdate")]
    logger.info(f"👥 Всего участников: {len(members)}, с датами рождения: {len(users_with_bdate)}")

    if not users_with_bdate:
        logger.info("🔍 У участников нет дат рождения")
        return

    # Получаем полные имена для пользователей с bdate
    user_ids = [m["id"] for m in users_with_bdate]
    users_info = await _get_users_info(user_ids)

    # Ищем именинников
    birthday_people = []
    for user in users_info:
        user_id = user.get("id")
        member = next((m for m in users_with_bdate if m["id"] == user_id), None)
        if not member:
            continue

        bdate = member.get("bdate")
        if not bdate:
            continue

        parsed = _parse_bdate(bdate)
        if parsed:
            day, month = parsed
            if day == today_day and month == today_month:
                first_name = user.get("first_name", "")
                last_name = user.get("last_name", "")
                name = f"{first_name} {last_name}".strip() or "Сталкер"
                birthday_people.append({
                    "id": user_id,
                    "name": name
                })

    if birthday_people:
        mentions = ", ".join(
            f"@id{p['id']} ({p['name']})" for p in birthday_people
        )
        message = BIRTHDAY_TEMPLATE.format(mentions=mentions)
        await _send_message(peer_id, message)
        logger.info(f"🎉 Именинники в peer_id={peer_id}: {len(birthday_people)} чел.")
        for p in birthday_people:
            logger.info(f"   🎂 {p['name']} (@id{p['id']})")
    else:
        logger.info(f"🔍 В peer_id={peer_id} именинников нет")