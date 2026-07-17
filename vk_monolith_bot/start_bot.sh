#!/bin/bash
# Скрипт запуска бота "Сота Сил"

# Получаем директорию, где находится этот скрипт
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Запуск бота 'Сота Сил'..."

# Активация виртуального окружения
source "$SCRIPT_DIR/venv/bin/activate"

# Запуск бота
python "$SCRIPT_DIR/bot.py"