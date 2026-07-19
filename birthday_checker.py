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
        "count": 50,
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
                logger.info(f"📋 Найдено {len(items)} бесед/чатов")
                # Ищем беседу (peer_id > 2000000000)
                for item in items:
                    peer = item.get("peer", {})
                    peer_id = peer.get("id")
                    logger.info(f"   🔍 Проверяю peer_id={peer_id}")
                    if peer_id and peer_id > 2000000000:
                        logger.info(f"✅ Найдена беседа: peer_id={peer_id}")
                        return peer_id
                logger.warning("⚠️ Беседы не найдены среди доступных чатов")
    return None


async def _get_group_members() -> list:
    """Получить список всех участников беседы с датами рождения"""
    # Получаем peer_id группового чата
    peer_id = await _get_group_chat_peer_id()
    if not peer_id:
        logger.warning("⚠️ Не удалось получить peer_id беседы")
        return []

    # Получаем список участников беседы
    all_user_ids = []
    offset = 0
    count = 1000

    while True:
        params = {
            "access_token": VK_TOKEN,
            "v": VK_API_VERSION,
            "peer_id": peer_id,
            "offset": offset,
            "count": count
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{VK_API_URL}messages.getConversationMembers",
                params=params
            ) as response:
                data = await response.json()
                if "error" in data:
                    logger.error(f"Ошибка получения участников беседы: {data['error']}")
                    return []
                if "response" in data:
                    response_data = data["response"]
                    if isinstance(response_data, dict):
                        members = response_data.get("members", [])
                        total = response_data.get("count", len(members))
                    else:
                        members = response_data
                        total = len(members)

                    for member in members:
                        user_id = member.get("member_id")
                        if user_id and user_id > 0:  # Только пользователи, не группы
                            all_user_ids.append({"id": user_id})
                    
                    logger.info(f"👥 Получено {len(all_user_ids)} участников беседы (из {total})")

                    if len(all_user_ids) >= total:
                        break
                    offset += count
                else:
                    break

    if not all_user_ids:
        logger.warning("⚠️ Не удалось получить участников беседы")
        return []

    # Теперь получаем даты рождения и имена через users.get (batch запрос)
    # users.get принимает до 250 user_ids в одном запросе
    all_members_with_bdate = []
    batch_size = 250
    
    for i in range(0, len(all_user_ids), batch_size):
        batch_ids = all_user_ids[i:i + batch_size]
        params = {
            "user_ids": ",".join(str(uid["id"]) for uid in batch_ids),
            "access_token": VK_TOKEN,
            "v": VK_API_VERSION,
            "fields": "bdate,first_name,last_name"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{VK_API_URL}users.get",
                params=params
            ) as response:
                data = await response.json()
                if "error" in data:
                    logger.error(f"Ошибка получения пользователей: {data['error']}")
                    continue
                if "response" in data:
                    users = data["response"]
                    for user in users:
                        user_id = user.get("id")
                        # Находим соответствующий элемент в all_user_ids
                        member = next((m for m in all_user_ids if m["id"] == user_id), None)
                        if member:
                            # Добавляем bdate и имена к существующему элементу
                            member["bdate"] = user.get("bdate")
                            member["first_name"] = user.get("first_name", "")
                            member["last_name"] = user.get("last_name", "")
                            all_members_with_bdate.append(member)
                        else:
                            # Если элемент не найден, создаём новый
                            all_members_with_bdate.append({
                                "id": user_id,
                                "bdate": user.get("bdate"),
                                "first_name": user.get("first_name", ""),
                                "last_name": user.get("last_name", "")
                            })

    logger.info(f"👥 Итого участников беседы с данными: {len(all_members_with_bdate)}")
    return all_members_with_bdate


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

    # Ищем именинников
    birthday_people = []
    for member in users_with_bdate:
        bdate = member.get("bdate")
        if not bdate:
            continue

        parsed = _parse_bdate(bdate)
        if parsed:
            day, month = parsed
            if day == today_day and month == today_month:
                first_name = member.get("first_name", "")
                last_name = member.get("last_name", "")
                name = f"{first_name} {last_name}".strip() or "Сталкер"
                birthday_people.append({
                    "id": member["id"],
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

    # Ищем именинников
    birthday_people = []
    for member in users_with_bdate:
        bdate = member.get("bdate")
        if not bdate:
            continue

        parsed = _parse_bdate(bdate)
        if parsed:
            day, month = parsed
            if day == today_day and month == today_month:
                first_name = member.get("first_name", "")
                last_name = member.get("last_name", "")
                name = f"{first_name} {last_name}".strip() or "Сталкер"
                birthday_people.append({
                    "id": member["id"],
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