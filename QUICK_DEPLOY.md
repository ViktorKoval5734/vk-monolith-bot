# 🚀 Быстрое развертывание с Docker

## ⚡ Быстрый старт (5 минут)

### 1. Подготовка сервера
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
# Перезайдите в систему или выполните:
newgrp docker
```

### 2. Загрузка файлов бота
```bash
# Создание директории
mkdir sota-bot && cd sota-bot

# Загрузка всех файлов проекта (или git clone)
# Скопируйте все файлы из локального проекта
```

### 3. Настройка переменных окружения
```bash
# Создание .env файла
nano .env
```

**Содержимое .env:**
```bash
# Токен сообщества ВКонтакте
VK_TOKEN=your_vk_token_here

# ID сообщества ВКонтакте
VK_GROUP_ID=your_group_id_here

# Секретный ключ для Callback API
CONFIRMATION_SECRET=your_secret_key_here

# Ключ авторизации Гигачата
GIGACHAT_AUTH_KEY=your_auth_key_here

# Client ID Гигачата
GIGACHAT_CLIENT_ID=your_client_id_here

# Scope для Гигачата
GIGACHAT_SCOPE=GIGACHAT_API_PERS

# Путь к файлу истории
HISTORY_FILE=history.json
```

### 4. Запуск бота
```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f sota-bot

# Проверка статуса
docker-compose ps
```

### 5. Настройка ВКонтакте
- **URL сервера:** `http://your-server-ip`
- **Секретный ключ:** тот же, что в .env
- **Версия API:** `5.199`

## 🔧 Управление

### Основные команды:
```bash
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Перезапуск
docker-compose restart

# Логи бота
docker-compose logs -f sota-bot

# Логи всех сервисов
docker-compose logs -f

# Обновление и перезапуск
docker-compose pull
docker-compose up -d
```

### Обновление бота:
```bash
# Остановка
docker-compose down

# Обновление кода (если используется git)
git pull

# Перезапуск
docker-compose up -d --build
```

## 🔒 Добавление SSL (Let's Encrypt)

```bash
# Остановка сервисов
docker-compose down

# Редактирование nginx.conf - раскомментируйте HTTPS секцию
nano nginx.conf

# Добавление SSL сертификата
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com

# Копирование сертификатов
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./ssl/key.pem

# Обновление прав доступа
sudo chown -R $USER:$USER ./ssl

# Запуск с HTTPS
docker-compose up -d
```

## 📊 Мониторинг

### Автоматический перезапуск:
```bash
# Создание скрипта мониторинга
nano monitor.sh
```

```bash
#!/bin/bash
cd /path/to/sota-bot
if ! docker-compose ps | grep -q "Up"; then
    echo "Bot is down, restarting..."
    docker-compose restart
fi
```

```bash
# Добавление в crontab
crontab -e
*/5 * * * * /path/to/sota-bot/monitor.sh >> /path/to/sota-bot/monitor.log 2>&1
```

## 🆘 Решение проблем

### Проверка логов:
```bash
# Все логи
docker-compose logs

# Логи конкретного сервиса
docker-compose logs sota-bot
docker-compose logs nginx
docker-compose logs redis
```

### Пересборка контейнера:
```bash
docker-compose up -d --build
```

### Очистка системы:
```bash
# Остановка и удаление всех контейнеров
docker-compose down -v

# Удаление неиспользуемых образов
docker system prune -a
```

## 💡 Дополнительно

### Backup данных:
```bash
# Создание резервной копии
tar -czf sota-bot-backup-$(date +%Y%m%d).tar.gz .env user_preferences.json history.json
```

### Восстановление:
```bash
# Остановка
docker-compose down

# Восстановление файлов
tar -xzf sota-bot-backup-YYYYMMDD.tar.gz

# Запуск
docker-compose up -d
```

---

**Готово! Бот работает 24/7 на сервере!** 🤖✨