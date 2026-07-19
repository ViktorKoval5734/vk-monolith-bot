"""
Проверка дней рождения участников бесед
Запускается ежедневно в 9:00 по МСК
"""
import logging
import asyncio
import aiohttp
import re
from datetime import datetime, timezone, timedelta
from config import VK_TOKEN, VK_API_URL, VK_API_VERSION, VK_GROUP_ID

logger = logging.getLogger(__name__)

# МСК = UTC+3
MSK_TZ = timezone(timedelta(hours=3))

# Поздравления
BIRTHDAY_TEMPLATE = "Сегодня в Зоне празднуют День Рождения! Сталкеры, поздравьте же братьев, что очередной год делят с вами консервы и патроны! {mentions}, с праздником!!!"


async def _get_group_members(peer_id: int = None) -> list:
    """Получить список всех участников беседы с датами рождения
    
    Args:
        peer_id: ID беседы. Если не указан, используется групповой чат.
    """
    all_user_ids = []
    
    # Если указан peer_id, используем getConversationMembers
    if peer_id and peer_id > 2000000000:
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
                        break
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
                            if user_id and user_id > 0:
                                all_user_ids.append({"id": user_id})
                        
                        logger.info(f"👥 Получено {len(all_user_ids)} участников беседы (из {total})")

                        if len(all_user_ids) >= total:
                            break
                        offset += count
                    else:
                        break
    else:
        # Fallback: используем groups.getMembers
        offset = 0
        count = 1000

        while True:
            params = {
                "access_token": VK_TOKEN,
                "v": VK_API_VERSION,
                "group_id": VK_GROUP_ID,
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
                        logger.error(f"Ошибка получения участников группы: {data['error']}")
                        break
                    if "response" in data:
                        response_data = data["response"]
                        if isinstance(response_data, dict):
                            members = response_data.get("items", [])
                            total = response_data.get("count", len(members))
                        else:
                            members = response_data
                            total = len(members)

                        all_user_ids.extend(members)
                        logger.info(f"👥 Получено {len(all_user_ids)} участников группы (из {total})")

                        if len(all_user_ids) >= total:
                            break
                        offset += count
                    else:
                        break

    if not all_user_ids:
        logger.warning("⚠️ Не удалось получить участников")
        return []

    # groups.getMembers возвращает список ID (int), преобразуем в список словарей
    if isinstance(all_user_ids[0], int):
        all_user_ids = [{"id": uid} for uid in all_user_ids]

    # Теперь получаем даты рождения и имена через users.get (batch запрос)
    # users.get принимает до 250 user_ids в одном запросе
    # Rate limit: 3 запроса в секунду для токена сообщества
    all_members_with_bdate = []
    batch_size = 250
    
    for i in range(0, len(all_user_ids), batch_size):
        batch_ids = all_user_ids[i:i + batch_size]
        params = {
            "user_ids": ",".join(str(uid["id"] if isinstance(uid, dict) else uid) for uid in batch_ids),
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
                        member = next((m for m in all_user_ids if (m.get("id") if isinstance(m, dict) else m) == user_id), None)
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

        # Rate limiting: 3 запроса в секунду
        if i + batch_size < len(all_user_ids):
            await asyncio.sleep(0.34)

    # Статистика
    with_bdate = [m for m in all_members_with_bdate if m.get("bdate")]
    without_bdate = [m for m in all_members_with_bdate if not m.get("bdate")]
    logger.info(f"👥 Итого участников с данными: {len(all_members_with_bdate)}")
    logger.info(f"📅 С датами рождения: {len(with_bdate)}, без дат: {len(without_bdate)}")
    if without_bdate:
        logger.info(f"⚠️ Участники без bdate: {[m.get('first_name', '?') for m in without_bdate[:10]]}")
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


async def get_todays_birthdays_message(peer_id: int = None) -> str:
    """
    Получить текст поздравления с днями рождения на сегодня.
    Возвращает текст поздравления или сообщение об отсутствии именинников.
    
    Args:
        peer_id: ID беседы для получения участников. Если не указан, используется группа.
    """
    now = datetime.now(MSK_TZ)
    today_day = now.day
    today_month = now.month

    logger.info(f"🎂 Ручная проверка дней рождения на {today_day}.{today_month:02d}...")

    # Получаем участников группы/беседы
    members = await _get_group_members(peer_id)
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

    # Получаем peer_id группового чата через searchChats
    peer_id = None
    
    # Получаем название группы
    async with aiohttp.ClientSession() as session:
        params = {
            "access_token": VK_TOKEN,
            "v": VK_API_VERSION,
            "group_ids": VK_GROUP_ID,
        }
        async with session.get(
            f"{VK_API_URL}groups.getById",
            params=params
        ) as response:
            data = await response.json()
            if "response" in data and data["response"]:
                group_name = data["response"][0].get("name", "")
                logger.info(f"📋 Название группы: {group_name}")
                
                # Ищем беседу по названию группы
                params = {
                    "access_token": VK_TOKEN,
                    "v": VK_API_VERSION,
                    "q": group_name,
                    "count": 10,
                }
                async with session.get(
                    f"{VK_API_URL}messages.searchChats",
                    params=params
                ) as response:
                    data = await response.json()
                    if "response" in data:
                        chats = data["response"]
                        logger.info(f"🔍 Найдено бесед по названию: {len(chats)}")
                        for chat in chats:
                            chat_id = chat.get("chat_id")
                            if chat_id:
                                peer_id = chat_id + 2000000000  # Конвертируем chat_id в peer_id
                                logger.info(f"✅ Найдена беседа: peer_id={peer_id}, name={chat.get('name')}")
                                break

    if not peer_id:
        logger.warning("⚠️ Не удалось найти групповой чат. Проверьте, что бот состоит в беседе.")
        return

    # Получаем участников группы
    members = await _get_group_members(peer_id)
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