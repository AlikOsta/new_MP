#!/bin/bash

# Скрипт для запуска Telegram бота
# Использование: ./run_bot.sh

echo "🤖 Запуск Telegram бота для Marketplace..."

# Проверяем переменные окружения
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ Переменная TELEGRAM_BOT_TOKEN не найдена"
    echo "Загружаем из backend/.env файла..."
fi

# Переходим в директорию проекта
cd /app

# Запускаем бота
python telegram_bot.py