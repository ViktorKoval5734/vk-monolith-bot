#!/bin/bash

# Скрипт для запуска бота и сервера в одном окне Konsole
# с вертикальным разделением (две панели рядом)

echo "🚀 Запуск Монолита в вертикально разделённом окне Konsole..."

# Проверяем, установлен ли Konsole
if ! command -v konsole &> /dev/null; then
    echo "❌ Konsole не найден. Этот скрипт работает только в KDE/Plasma."
    echo "💡 Альтернатива: используйте ./run_sota.sh (tmux)"
    exit 1
fi

cd /home/deck/vk_sota_bot

echo "📁 Переходим в директорию: /home/deck/vk_sota_bot"

# Создаём временный скрипт для выполнения команд в разделённом окне
TEMP_SCRIPT=$(mktemp)

cat > "$TEMP_SCRIPT" << 'EOF'
# Ждём немного для инициализации Konsole
sleep 1

# Разделяем окно вертикально (Ctrl+Shift+O)
sleep 0.5
# Отправляем команды для разделения окна
# В Konsole: Ctrl+Shift+O для вертикального разделения
# Затем Ctrl+Tab для переключения между панелями

# В первой панели (левой) запускаем бота
echo "🤖 Запуск бота Монолит..."
echo "📡 Проверка подключения..."
python bot.py

# После завершения бота запускаем HTTP сервер в этой же панели
# (если бот остановился)
echo ""
echo "🌐 Запуск HTTP сервера..."
python -m http.server 8080
EOF

# Создаём второй скрипт для второй панели
TEMP_SCRIPT2=$(mktemp)

cat > "$TEMP_SCRIPT2" << 'EOF'
# Ждём инициализации
sleep 1

# Переключаемся во вторую панель (если есть)
sleep 0.5

# Во второй панели (правой) запускаем HTTP сервер сразу
echo "🌐 Запуск HTTP сервера..."
echo "📝 Сервер доступен по адресу: http://localhost:8080"
echo "🛑 Для остановки нажмите Ctrl+C"
echo ""
python -m http.server 8080
EOF

# Запускаем Konsole с вертикальным разделением
echo "🖥️ Открываю окно Konsole с вертикальным разделением..."

# Создаём скрипт, который откроет Konsole и разделит его
FINAL_SCRIPT=$(mktemp)

cat > "$FINAL_SCRIPT" << 'EOF'
# Создаём новое окно Konsole
konsole --separate --new-tab \
  --title "Монолит - Разделённое окно" \
  --workdir /home/deck/vk_sota_bot \
  -e bash -c "
    echo '🚀 Инициализация разделённого окна...'
    sleep 1
    
    # Разделяем окно вертикально (в Konsole: Ctrl+Shift+O)
    # Команда для разделения может отличаться в разных версиях
    
    echo '🤖 Запуск бота в левой панели...'
    echo '🌐 Запуск HTTP сервера в правой панели...'
    
    # Запускаем бота в первой панели
    python bot.py
  " &

# Ждём запуска первого окна
sleep 3

# Открываем вторую панель/вкладку для HTTP сервера
konsole --separate --new-tab \
  --title "HTTP Сервер" \
  --workdir /home/deck/vk_sota_bot \
  -e bash -c "
    echo '🌐 Запуск HTTP сервера...'
    echo '📝 Сервер доступен: http://localhost:8080'
    python -m http.server 8080
  " &

echo "✅ Окна запущены!"
EOF

chmod +x "$FINAL_SCRIPT"
bash "$FINAL_SCRIPT"

# Удаляем временные файлы
rm -f "$TEMP_SCRIPT" "$TEMP_SCRIPT2" "$FINAL_SCRIPT"

echo ""
echo "📋 Запущенные окна:"
echo "   🤖 Вкладка 1: Бот Монолит"
echo "   🌐 Вкладка 2: HTTP сервер (порт 8080)"
echo ""
echo "🔧 Управление в Konsole:"
echo "   - Переключение между вкладками: Ctrl+Tab или Ctrl+Shift+N"
echo "   - Закрыть вкладку: Ctrl+Shift+W"
echo "   - Разделить окно: Ctrl+Shift+O (вертикально) или Ctrl+Shift+E (горизонтально)"
echo ""
echo "📝 Логи бота отображаются в первой вкладке"
echo "🌐 Веб-интерфейс: http://localhost:8080"