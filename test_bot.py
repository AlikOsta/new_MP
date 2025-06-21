#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы Telegram бота
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Загружаем переменные
load_dotenv('backend/.env')
load_dotenv('frontend/.env')
load_dotenv('.env')

async def test_bot_components():
    """Тестируем компоненты бота"""
    
    print("🧪 Тестирование компонентов Telegram бота...")
    
    # 1. Проверяем переменные окружения
    print("\n1. Проверка переменных окружения:")
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    payment_token = os.getenv('TELEGRAM_PAYMENTS_TOKEN')
    backend_url = os.getenv('REACT_APP_BACKEND_URL')
    
    print(f"   BOT_TOKEN: {'✅ Найден' if bot_token else '❌ Не найден'}")
    print(f"   PAYMENT_TOKEN: {'✅ Найден' if payment_token else '❌ Не найден'}")
    print(f"   BACKEND_URL: {backend_url or '❌ Не найден'}")
    
    if not bot_token or not payment_token:
        print("❌ Отсутствуют необходимые токены!")
        return False
    
    # 2. Проверяем импорт telegram-bot
    print("\n2. Проверка импорта python-telegram-bot:")
    try:
        from telegram import Bot
        print("   ✅ python-telegram-bot импортирован успешно")
    except ImportError as e:
        print(f"   ❌ Ошибка импорта: {e}")
        return False
    
    # 3. Проверяем httpx для запросов к backend
    print("\n3. Проверка httpx:")
    try:
        import httpx
        print("   ✅ httpx импортирован успешно")
    except ImportError as e:
        print(f"   ❌ Ошибка импорта: {e}")
        return False
    
    # 4. Проверяем соединение с backend API
    print("\n4. Проверка соединения с backend:")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{backend_url}/api/health")
            if response.status_code == 200:
                print("   ✅ Backend API отвечает")
                data = response.json()
                print(f"   📊 Версия API: {data.get('version', 'unknown')}")
            else:
                print(f"   ❌ Backend API ошибка: {response.status_code}")
                return False
    except Exception as e:
        print(f"   ❌ Ошибка соединения с backend: {e}")
        return False
    
    # 5. Проверяем API тарифов
    print("\n5. Проверка API тарифов:")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{backend_url}/api/categories/all")
            if response.status_code == 200:
                data = response.json()
                packages = data.get('packages', [])
                print(f"   ✅ Найдено тарифов: {len(packages)}")
                
                for pkg in packages[:3]:  # Показываем первые 3
                    print(f"   📦 {pkg['name_ru']} - {pkg['price']} RUB")
            else:
                print(f"   ❌ Ошибка получения тарифов: {response.status_code}")
                return False
    except Exception as e:
        print(f"   ❌ Ошибка получения тарифов: {e}")
        return False
    
    # 6. Проверяем создание Bot объекта
    print("\n6. Проверка создания Bot объекта:")
    try:
        bot = Bot(token=bot_token)
        print("   ✅ Bot объект создан успешно")
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        print(f"   🤖 Имя бота: @{bot_info.username}")
        print(f"   🆔 ID бота: {bot_info.id}")
        
    except Exception as e:
        print(f"   ❌ Ошибка создания бота: {e}")
        return False
    
    print("\n✅ Все компоненты бота протестированы успешно!")
    print("\n📝 Для запуска бота используйте:")
    print("   python telegram_bot.py")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_bot_components())
    sys.exit(0 if success else 1)