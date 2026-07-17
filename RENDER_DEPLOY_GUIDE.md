# Деплой бота Монолит на Render.com

## 🎯 Почему Render.com отлично подходит для бота:

- ✅ **Бесплатный SSL** (HTTPS) - обязательно для Callback API ВКонтакте
- ✅ **Автоматический деплой** из Git репозитория
- ✅ **Environment Variables** для токенов
- ✅ **Статический IP** для настройки Callback API
- ✅ **Python поддержка** из коробки

## 🚀 Пошаговая инструкция

### 1. Подготовка репозитория

Создайте репозиторий на GitHub/GitLab и загрузите файлы бота:
```
vk_sota_bot/
├── bot.py
├── config.py
├── gigachat_client.py
├── history.py
├── user_preferences.py
├── requirements.txt
├── .env.example
└── render.yaml
```

### 2. Создайте файл render.yaml

```yaml
services:
  - type: web
    name: sota-sil-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn bot:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: VK_TOKEN
        fromService:
          type: envVarGroup
          name: vk-bot-env
          property: VK_TOKEN
      - key: VK_GROUP_ID
        fromService:
          type: envVarGroup
          name: vk-bot-env
          property: VK_GROUP_ID
      - key: GIGACHAT_AUTH_KEY
        fromService:
          type: envVarGroup
          name: vk-bot-env
          property: GIGACHAT_AUTH_KEY
      - key: GIGACHAT_CLIENT_ID
        fromService:
          type: envVarGroup
          name: vk-bot-env
          property: GIGACHAT_CLIENT_ID
      - key: CONFIRMATION_SECRET
        fromService:
          type: envVarGroup
          name: vk-bot-env
          property: CONFIRMATION_SECRET
```

### 3. Измените bot.py для Render

Нужно добавить поддержку переменной `$PORT`:

```python
import os
port = int(os.environ.get('PORT', 8000))

if __name__ == "__main__":
    import uvicorn
    config = uvicorn.Config(app, host="0.0.0.0", port=port)
    server = uvicorn.Server(config)
    server.run()
```

### 4. Создайте .env.example (обновлённый)

```env
# Токен сообщества ВКонтакте
VK_TOKEN=your_vk_token_here

# ID сообщества ВКонтакте
VK_GROUP_ID=your_group_id_here

# Секретный ключ для Callback API
CONFIRMATION_SECRET=your_secret_key_here

# Ключ авторизации Гигачата (Authorization key)
GIGACHAT_AUTH_KEY=your_gigachat_auth_key_here

# Client ID Гигачата
GIGACHAT_CLIENT_ID=your_gigachat_client_id_here

# Scope для Гигачата
GIGACHAT_SCOPE=GIGACHAT_API_PERS
```

### 5. Настройка на Render.com

1. **Зайдите на [render.com](https://render.com)**
2. **Подключите GitHub/GitLab аккаунт**
3. **Создайте новый Web Service**
4. **Выберите репозиторий с ботом**
5. **Настройте параметры:**
   - **Name:** `sota-sil-bot` (или любое имя)
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn bot:app --host 0.0.0.0 --port $PORT`

### 6. Настройка Environment Variables

В панели Render создайте Env Var Group `vk-bot-env` со всеми токенами:
- VK_TOKEN
- VK_GROUP_ID
- GIGACHAT_AUTH_KEY
- GIGACHAT_CLIENT_ID
- CONFIRMATION_SECRET

### 7. Настройка ВКонтакте Callback API

После деплоя получите HTTPS URL от Render:
```
https://sota-sil-bot.onrender.com
```

В настройках сообщества ВКонтакте:
- **Адрес сервера:** `https://sota-sil-bot.onrender.com`
- **Секретный ключ:** ваш `CONFIRMATION_SECRET`
- **Версия API:** `5.199`
- **Типы событий:** `message_new`

### 8. Деплой

1. Нажмите **"Create Web Service"**
2. Render автоматически соберёт и задеплоит бота
3. Получите HTTPS URL
4. Настройте Callback API в ВКонтакте
5. Подтвердите настройки

## ⚠️ Важные особенности

### **Бесплатные ограничения Render:**
- **Сервер "засыпает"** через 15 минут неактивности
- **Первый запрос** после сна может занять 30-60 секунд
- **Подходит для ботов** с низкой активностью

### **Решение для постоянной работы:**
- **Upgrade до платного плана** ($7/месяц) для постоянной работы
- **Или используйте другой сервис** с постоянными серверами

## 🔧 Альтернативы для постоянной работы

1. **Railway** - похоже на Render, но дороже
2. **Heroku** - классический, но дорогой
3. **DigitalOcean App Platform** - от $5/месяц
4. **VPS** - полный контроль, от $3-5/месяц

## 📝 Логи и мониторинг

В панели Render доступны:
- **Логи сборки и работы**
- **Метрики использования**
- **Статус сервиса**
- **URL для мониторинга**

## ✅ Готово!

После настройки ваш бот будет доступен по HTTPS URL и готов принимать сообщения от ВКонтакте!