#!/bin/bash
# Скрипт автоматического развертывания бота "Сота Сил"

set -e

echo "🚀 Запуск развертывания бота 'Сота Сил'..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Проверка прав суперпользователя
if [[ $EUID -eq 0 ]]; then
   warning "Не рекомендуется запускать скрипт от root. Создаём пользователя 'sota'..."
   
   # Создание пользователя sota
   if ! id "sota" &>/dev/null; then
       useradd -m -s /bin/bash sota
       usermod -aG sudo sota
       success "Пользователь 'sota' создан"
   fi
   
   # Переключение на пользователя sota
   log "Переключение на пользователя 'sota'..."
   exec sudo -u sota -i bash "$0" "$@"
fi

# Проверка ОС
if ! command -v apt &> /dev/null; then
    error "Скрипт поддерживает только Ubuntu/Debian с apt"
fi

# Обновление системы
log "Обновление системы..."
sudo apt update && sudo apt upgrade -y
success "Система обновлена"

# Установка базовых пакетов
log "Установка базовых пакетов..."
sudo apt install -y curl wget git nginx certbot python3-certbot-nginx ufw fail2ban
success "Базовые пакеты установлены"

# Установка Docker
log "Установка Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    success "Docker установлен"
else
    success "Docker уже установлен"
fi

# Установка Docker Compose
log "Установка Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    success "Docker Compose установлен"
else
    success "Docker Compose уже установлен"
fi

# Создание директории проекта
PROJECT_DIR="/home/$USER/vk_sota_bot"
if [ ! -d "$PROJECT_DIR" ]; then
    log "Создание директории проекта..."
    mkdir -p "$PROJECT_DIR"
    success "Директория создана: $PROJECT_DIR"
else
    log "Директория проекта уже существует: $PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# Проверка наличия файлов проекта
if [ ! -f "bot.py" ]; then
    warning "Файлы проекта не найдены в $PROJECT_DIR"
    warning "Убедитесь, что скопировали все файлы проекта в эту директорию:"
    warning "- bot.py"
    warning "- gigachat_client.py"
    warning "- history.py"
    warning "- config.py"
    warning "- user_preferences.py"
    warning "- requirements.txt"
    warning "- .env.example"
    warning ""
    warning "Скопируйте файлы и запустите скрипт снова."
    exit 1
fi

# Создание .env файла
if [ ! -f ".env" ]; then
    log "Создание .env файла..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        warning "Создан файл .env из .env.example"
        warning "⚠️  ВАЖНО: Отредактируйте .env файл и укажите ваши токены!"
        warning "Команда: nano .env"
    else
        cat > .env << EOF
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
EOF
        warning "Создан базовый .env файл"
        warning "⚠️  ВАЖНО: Отредактируйте .env файл и укажите ваши токены!"
        warning "Команда: nano .env"
    fi
else
    success ".env файл уже существует"
fi

# Создание базовых файлов Docker
if [ ! -f "Dockerfile" ]; then
    log "Создание Dockerfile..."
    cat > Dockerfile << 'EOF'
FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

EXPOSE 8000
CMD ["python", "bot.py"]
EOF
fi

if [ ! -f "docker-compose.yml" ]; then
    log "Создание docker-compose.yml..."
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  sota-bot:
    build: .
    container_name: sota-bot
    restart: unless-stopped
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./.env:/app/.env:ro
      - ./user_preferences.json:/app/user_preferences.json
      - ./history.json:/app/history.json
    networks:
      - sota-network

  nginx:
    image: nginx:alpine
    container_name: sota-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    networks:
      - sota-network
    depends_on:
      - sota-bot

networks:
  sota-network:
    driver: bridge
EOF
fi

if [ ! -f "nginx.conf" ]; then
    log "Создание nginx.conf..."
    cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream sota_bot {
        server sota-bot:8000;
    }

    server {
        listen 80;
        server_name _;

        location / {
            proxy_pass http://sota_bot;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        location /health {
            proxy_pass http://sota_bot;
            access_log off;
        }
    }
}
EOF
fi

# Создание файлов пользователя
if [ ! -f "user_preferences.json" ]; then
    echo '{}' > user_preferences.json
fi

if [ ! -f "history.json" ]; then
    echo '{}' > history.json
fi

# Настройка firewall
log "Настройка firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable
success "Firewall настроен"

# Создание скрипта управления
log "Создание скриптов управления..."
cat > manage.sh << 'EOF'
#!/bin/bash
# Скрипт управления ботом "Сота Сил"

case "$1" in
    start)
        echo "🚀 Запуск бота..."
        docker-compose up -d
        ;;
    stop)
        echo "🛑 Остановка бота..."
        docker-compose down
        ;;
    restart)
        echo "🔄 Перезапуск бота..."
        docker-compose restart
        ;;
    logs)
        echo "📋 Логи бота:"
        docker-compose logs -f sota-bot
        ;;
    status)
        echo "📊 Статус сервисов:"
        docker-compose ps
        ;;
    update)
        echo "🔄 Обновление и перезапуск..."
        docker-compose pull
        docker-compose up -d --build
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|logs|status|update}"
        exit 1
        ;;
esac
EOF

chmod +x manage.sh

# Запуск бота
log "Запуск бота..."
docker-compose up -d

# Проверка статуса
sleep 5
if docker-compose ps | grep -q "Up"; then
    success "🎉 Бот успешно развёрнут и запущен!"
    echo ""
    echo "📋 Информация о развертывании:"
    echo "   📁 Директория: $PROJECT_DIR"
    echo "   🌐 URL: http://$(curl -s ifconfig.me 2>/dev/null || echo 'your-server-ip')"
    echo "   📝 Логи: ./manage.sh logs"
    echo "   🔧 Управление: ./manage.sh {start|stop|restart|logs|status|update}"
    echo ""
    echo "⚠️  ВАЖНЫЕ ШАГИ:"
    echo "   1. Отредактируйте .env файл с вашими токенами"
    echo "   2. Настройте Callback API в ВКонтакте"
    echo "   3. При необходимости настройте домен и SSL"
    echo ""
    echo "🔗 Настройки ВКонтакте:"
    echo "   URL: http://$(curl -s ifconfig.me 2>/dev/null || echo 'your-server-ip')"
    echo "   Секретный ключ: (указан в .env файле)"
    echo ""
else
    error "Ошибка запуска бота. Проверьте логи: docker-compose logs"
fi

success "Развертывание завершено!"