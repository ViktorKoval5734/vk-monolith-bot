# 🚀 Развертывание бота "Монолит" на серверe

## 📋 Что потребуется:
- VPS/VDS сервер (Ubuntu 20.04/22.04 или Debian 11+)
- Домен (опционально, но рекомендуется)
- Доступ по SSH

## 🏗️ Пошаговая инструкция

### Шаг 1: Аренда VPS

**Рекомендуемые провайдеры:**
- **Timeweb** (Россия) - от 300₽/месяц
- **Hetzner** (Германия) - от €3.19/месяц
- **DigitalOcean** - от $4/месяц
- **Vultr** - от $3.50/месяц

**Минимальные требования:**
- 1 CPU, 1GB RAM, 20GB SSD
- Ubuntu 20.04+ или Debian 11+

### Шаг 2: Подключение к серверу

```bash
# Подключение по SSH (замените IP на ваш)
ssh root@your_server_ip
```

### Шаг 3: Обновление системы

```bash
# Обновление пакетов
apt update && apt upgrade -y

# Установка базовых пакетов
apt install -y curl wget git nginx certbot python3-certbot-nginx ufw
```

### Шаг 4: Установка Python и зависимостей

```bash
# Установка Python и pip
apt install -y python3 python3-pip python3-venv

# Проверка версии Python
python3 --version
```

### Шаг 5: Создание пользователя для бота

```bash
# Создание пользователя
useradd -m -s /bin/bash sota
usermod -aG sudo sota

# Переключение на пользователя
su - sota
```

### Шаг 6: Загрузка кода бота

```bash
# Переход в домашнюю директорию
cd /home/sota

# Клонирование репозитория (или загрузка файлов)
# Если у вас есть репозиторий:
git clone https://github.com/your_username/vk_sota_bot.git

# Или создание директории вручную:
mkdir vk_sota_bot
cd vk_sota_bot

# Загрузка файлов через scp или git
```

### Шаг 7: Настройка виртуального окружения

```bash
# Создание виртуального окружения
python3 -m venv venv

# Активация окружения
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### Шаг 8: Настройка переменных окружения

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

### Шаг 9: Создание systemd сервиса

```bash
# Возврат к root
exit

# Создание файла сервиса
nano /etc/systemd/system/sota-bot.service
```

**Содержимое sota-bot.service:**
```ini
[Unit]
Description=Sota Sil VK Bot
After=network.target

[Service]
Type=simple
User=sota
WorkingDirectory=/home/sota/vk_sota_bot
Environment=PATH=/home/sota/vk_sota_bot/venv/bin
ExecStart=/home/sota/vk_sota_bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Перезагрузка systemd
systemctl daemon-reload

# Включение автозапуска сервиса
systemctl enable sota-bot

# Запуск сервиса
systemctl start sota-bot

# Проверка статуса
systemctl status sota-bot
```

### Шаг 10: Настройка Nginx

```bash
# Создание конфигурации сайта
nano /etc/nginx/sites-available/sota-bot
```

**Содержимое конфигурации:**
```nginx
server {
    listen 80;
    server_name your-domain.com;  # Замените на ваш домен или IP

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Активация конфигурации
ln -s /etc/nginx/sites-available/sota-bot /etc/nginx/sites-enabled/

# Тест конфигурации
nginx -t

# Перезагрузка Nginx
systemctl reload nginx
```

### Шаг 11: Настройка домена (опционально)

```bash
# Если у вас есть домен, укажите A-запись на IP сервера
# Затем получите SSL сертификат:
certbot --nginx -d your-domain.com
```

### Шаг 12: Настройка firewall

```bash
# Настройка UFW
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80
ufw allow 443
ufw enable

# Проверка статуса
ufw status
```

## 🔧 Управление ботом

### Команды управления:
```bash
# Запуск бота
sudo systemctl start sota-bot

# Остановка бота
sudo systemctl stop sota-bot

# Перезапуск бота
sudo systemctl restart sota-bot

# Просмотр логов
sudo journalctl -u sota-bot -f

# Просмотр статуса
sudo systemctl status sota-bot
```

### Обновление кода:
```bash
# Остановка сервиса
sudo systemctl stop sota-bot

# Переход в директорию
cd /home/sota/vk_sota_bot

# Обновление кода (если используется git)
git pull

# Обновление зависимостей (если нужно)
source venv/bin/activate
pip install -r requirements.txt

# Запуск сервиса
sudo systemctl start sota-bot
```

## 📊 Мониторинг

### Автоматический мониторинг:
```bash
# Создание скрипта мониторинга
nano /home/sota/monitor.sh
```

```bash
#!/bin/bash
# Проверка работы бота
if ! systemctl is-active --quiet sota-bot; then
    echo "Bot is down, restarting..."
    systemctl restart sota-bot
fi
```

```bash
# Добавление в crontab (проверка каждые 5 минут)
crontab -e

# Добавить строку:
*/5 * * * * /home/sota/monitor.sh >> /home/sota/monitor.log 2>&1
```

## 🔒 Безопасность

### Рекомендации:
1. **Используйте SSH ключи** вместо паролей
2. **Отключите root доступ** по SSH
3. **Регулярно обновляйте** систему
4. **Используйте strong passwords** для .env
5. **Настройте fail2ban** для защиты от брутфорса

### Отключение root SSH:
```bash
# Редактирование конфигурации SSH
nano /etc/ssh/sshd_config

# Изменить:
PermitRootLogin no

# Перезапуск SSH
systemctl restart ssh
```

## 🌐 Настройка Callback API в ВКонтакте

После развертывания:
1. **URL сервера:** `https://your-domain.com` (или IP)
2. **Секретный ключ:** тот же, что в .env
3. **Версия API:** `5.199`

## 🆘 Решение проблем

### Бот не отвечает:
```bash
# Проверка логов
sudo journalctl -u sota-bot -f

# Проверка портов
netstat -tlnp | grep 8000

# Проверка Nginx
sudo nginx -t
```

### Проблемы с SSL:
```bash
# Обновление сертификата
certbot renew

# Принудительное обновление
certbot renew --force-renewal
```

---

## 💡 Дополнительные возможности

### Docker развертывание:
Создайте Dockerfile для контейнеризации.

### CI/CD:
Настройте GitHub Actions для автоматического деплоя.

### Backup:
Регулярно создавайте резервные копии .env и user_preferences.json.

**Бот будет работать 24/7 автоматически!** 🤖✨