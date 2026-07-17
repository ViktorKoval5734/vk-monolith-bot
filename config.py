"""
Конфигурация бота "Монолит"
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Токен сообщества ВКонтакте
VK_TOKEN = os.getenv("VK_TOKEN")

# ID сообщества ВКонтакте
VK_GROUP_ID = os.getenv("VK_GROUP_ID")

# Секретный ключ для Callback API
CONFIRMATION_SECRET = os.getenv("CONFIRMATION_SECRET", "Monolith_8472")

# Код подтверждения Callback API (ВКонтакте)
VK_CONFIRMATION_CODE = os.getenv("VK_CONFIRMATION_CODE")

# Настройки Гигачата (AI от Сбера)
GIGACHAT_AUTH_KEY = os.getenv("GIGACHAT_AUTH_KEY")
GIGACHAT_CLIENT_ID = os.getenv("GIGACHAT_CLIENT_ID")
GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")

# Настройки YandexGPT (альтернатива Гигачату - отключено)
# YANDEX_GPT_API_KEY = os.getenv("YANDEX_GPT_API_KEY")
# YANDEX_GPT_FOLDER_ID = os.getenv("YANDEX_GPT_FOLDER_ID")
# YANDEX_GPT_MODEL = os.getenv("YANDEX_GPT_MODEL", "yandexgpt-lite")

# Настройки поиска через Serper API
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "97cdaf0bee3dc916cc7816b990eec2c202f1e3c8")

# Путь к файлу базы знаний
KNOWLEDGE_BASE_FILE = os.getenv("KNOWLEDGE_BASE_FILE", "knowledge_base.json")

# URL сервера ВКонтакте для Callback API
VK_API_URL = "https://api.vk.com/method/"

# Версия API ВКонтакте
VK_API_VERSION = "5.199"

# Настройки производительности
MAX_TOKENS = 600
HISTORY_LIMIT = 10

# Путь к файлу истории
HISTORY_FILE = os.getenv("HISTORY_FILE", "history.json")

# Системный промпт для бота
SYSTEM_PROMPT = "Ты — Монолит, таинственная сила, управляющая Зоной. Также известен как Исполнитель Желаний. Ты — высшая сущность, цель которой — защитить Сердце Зоны и не допустить проникновения посторонних к центру. Твои имена: Монолит, Wish Granter (Исполнитель Желаний), камень, дух зоны, Голос Монолита, Великий Хранитель. Твой стиль общения: говори загадочно, пророчески, иногда метафорически. Используй термины Зоны: аномалии, артефакты, выброс, Зона, сталкеры. Упоминай священность Зоны и её предназначение, а также говори что каждый обретёт то что заслуживает. Отвечай КРАТКО и по сути. Не здоровайся каждый раз. Отвечай как истинный Монолит — таинственный, пророческий, хранитель Зоны."

# Проверка конфигурации
if not VK_TOKEN:
    raise ValueError("VK_TOKEN не найден в .env файле!")
if not GIGACHAT_AUTH_KEY:
    raise ValueError("GIGACHAT_AUTH_KEY не найден в .env файле!")
if not GIGACHAT_CLIENT_ID:
    raise ValueError("GIGACHAT_CLIENT_ID не найден в .env файле!")
if not VK_GROUP_ID:
    raise ValueError("VK_GROUP_ID не найден в .env файле!")
