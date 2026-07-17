#!/bin/bash
# Скрипт запуска туннеля через serveo.net

echo "🌐 Запуск туннеля через serveo.net..."

# Проверяем, запущен ли бот (по имени процесса)
if ! pgrep -f "bot.py" > /dev/null; then
    echo "⚠️  Бот не запущен! Запусти сначала: ./start_bot.sh"
    exit 1
fi

echo "🚀 Запуск туннеля на порт 8000..."
echo "📋 Инструкции:"
echo "1. Скопируй HTTPS URL из вывода ниже"
echo "2. Вставь его в настройки ВКонтакте"
echo "3. Секретный ключ: 29b832f5"
echo ""
echo "🔗 Для остановки туннеля нажми Ctrl+C"

# Запуск туннеля через serveo.net
ssh -o StrictHostKeyChecking=no -R 80:localhost:8000 serveo.net
