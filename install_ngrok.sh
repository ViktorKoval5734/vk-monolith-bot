#!/bin/bash
# Скрипт установки ngrok

echo "🔧 Установка ngrok..."

# Скачивание ngrok
cd /home/deck
wget --no-check-certificate -O ngrok.tgz https://bin.equinox.io/a/76vdzhNjs7e/ngrok-v3-3.35.0-linux-amd64.tgz

if [ $? -eq 0 ]; then
    echo "✅ Скачивание завершено"
    
    # Распаковка
    tar xzf ngrok.tgz
    
    # Перемещение в систему
    sudo mv ngrok /usr/local/bin
    
    # Проверка установки
    ngrok --version
    
    echo "🎉 ngrok установлен! Запусти: ngrok http 800"
else
    echo "❌ Ошибка скачивания"
fi