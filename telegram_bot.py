"""
Telegram Bot для Telegram Marketplace Mini App
Упрощенная версия с совместимыми зависимостями
"""

import asyncio
import os
import logging
from typing import Dict, Any
import json

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    WebAppInfo, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    LabeledPrice,
    PreCheckoutQuery,
    SuccessfulPayment
)
import httpx
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('.env')
load_dotenv('backend/.env')

# Конфигурация
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PAYMENT_PROVIDER_TOKEN = os.getenv('TELEGRAM_PAYMENTS_TOKEN')
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://958e1ad6-00a3-4c3e-a8b5-fdd4fba26a4a.preview.emergentagent.com')
MINIAPP_URL = BACKEND_URL  # Mini App URL - тот же домен, что и backend

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class TelegramMarketplaceBot:
    """Основной класс Telegram бота для маркетплейса"""
    
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.payment_provider_token = PAYMENT_PROVIDER_TOKEN
    
    async def call_backend_api(self, endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Вызов API бэкенда"""
        try:
            url = f"{self.backend_url}/api{endpoint}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                if method == "GET":
                    response = await client.get(url)
                elif method == "POST":
                    response = await client.post(url, json=data)
                elif method == "PUT":
                    response = await client.put(url, json=data)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Backend API error: {response.status_code} - {response.text}")
                    return {}
        except Exception as e:
            logger.error(f"Error calling backend API: {str(e)}")
            return {}
    
    async def get_package_info(self, package_id: str) -> Dict[str, Any]:
        """Получить информацию о тарифе"""
        packages = await self.call_backend_api("/categories/all")
        if packages and "packages" in packages:
            for package in packages["packages"]:
                if package["id"] == package_id:
                    return package
        return {}
    
    async def create_payment_invoice(self, user_id: int, package_id: str, chat_id: int):
        """Создать инвойс для оплаты тарифа"""
        try:
            # Получаем информацию о тарифе
            package_info = await self.get_package_info(package_id)
            
            if not package_info:
                await bot.send_message(chat_id, "❌ Тариф не найден")
                return
            
            # Создаем payload для связки с backend
            payload = f"package_{package_id}_{user_id}"
            
            # Цена в копейках (для RUB)
            price_kopecks = int(package_info["price"] * 100)
            
            # Отправляем инвойс
            await bot.send_invoice(
                chat_id=chat_id,
                title=f"Тариф: {package_info['name_ru']}",
                description=f"Покупка тарифа для публикации объявления\n{package_info.get('features_ru', '')}",
                payload=payload,
                provider_token=self.payment_provider_token,
                currency="RUB",
                prices=[
                    LabeledPrice(
                        label=package_info['name_ru'], 
                        amount=price_kopecks
                    )
                ],
                start_parameter="marketplace_payment",
                need_email=False,
                need_phone_number=False,
                need_name=False,
                need_shipping_address=False,
                is_flexible=False
            )
            
            logger.info(f"Invoice sent for package {package_id} to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error creating payment invoice: {str(e)}")
            await bot.send_message(chat_id, "❌ Ошибка при создании счета для оплаты")

# Инициализируем бота
marketplace_bot = TelegramMarketplaceBot()

@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message):
    """
    Хендлер для команды /start: отправляет кнопку для открытия Mini App
    """
    try:
        # Кнопка для открытия Mini App
        webapp_button = InlineKeyboardButton(
            text="🚀 Открыть Маркетплейс",
            web_app=WebAppInfo(url=MINIAPP_URL)
        )
        
        # Кнопка для получения помощи
        help_button = InlineKeyboardButton(
            text="❓ Помощь",
            callback_data="help"
        )
        
        # Собираем клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [webapp_button],
            [help_button]
        ])
        
        # Приветственное сообщение
        welcome_text = (
            "🎯 <b>Добро пожаловать в Telegram Маркетплейс!</b>\n\n"
            "📱 Здесь вы можете:\n"
            "• Найти работу или услуги\n"
            "• Разместить свое объявление\n"
            "• Купить тарифы для продвижения\n\n"
            "👆 Нажмите кнопку ниже, чтобы открыть приложение:"
        )
        
        await message.answer(
            text=welcome_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        logger.info(f"Start command processed for user {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Error in start command: {str(e)}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")

@dp.callback_query(lambda c: c.data == "help")
async def process_help_callback(callback_query: types.CallbackQuery):
    """Обработка кнопки помощи"""
    help_text = (
        "❓ <b>Помощь по использованию маркетплейса</b>\n\n"
        "🔹 <b>Как найти работу/услугу:</b>\n"
        "• Откройте приложение\n"
        "• Выберите категорию (Работа/Услуги)\n"
        "• Используйте поиск и фильтры\n\n"
        "🔹 <b>Как разместить объявление:</b>\n"
        "• Нажмите кнопку '+' в приложении\n"
        "• Заполните информацию\n"
        "• Выберите тариф\n\n"
        "🔹 <b>Тарифы:</b>\n"
        "• Бесплатный - 1 объявление в неделю\n"
        "• Платные - больше возможностей и продвижение\n\n"
        "💬 По вопросам: @support"
    )
    
    await callback_query.message.edit_text(
        text=help_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_start")]
        ]),
        parse_mode="HTML"
    )

@dp.callback_query(lambda c: c.data == "back_to_start")
async def process_back_to_start(callback_query: types.CallbackQuery):
    """Возврат к стартовому сообщению"""
    webapp_button = InlineKeyboardButton(
        text="🚀 Открыть Маркетплейс",
        web_app=WebAppInfo(url=MINIAPP_URL)
    )
    
    help_button = InlineKeyboardButton(
        text="❓ Помощь",
        callback_data="help"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [webapp_button],
        [help_button]
    ])
    
    welcome_text = (
        "🎯 <b>Добро пожаловать в Telegram Маркетплейс!</b>\n\n"
        "📱 Здесь вы можете:\n"
        "• Найти работу или услуги\n"
        "• Разместить свое объявление\n"
        "• Купить тарифы для продвижения\n\n"
        "👆 Нажмите кнопку ниже, чтобы открыть приложение:"
    )
    
    await callback_query.message.edit_text(
        text=welcome_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@dp.message(Command(commands=["pay"]))
async def cmd_pay(message: types.Message):
    """
    Команда для тестирования платежей (только для разработки)
    Использование: /pay package_id
    """
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.answer("Использование: /pay package_id")
            return
        
        package_id = args[1]
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        await marketplace_bot.create_payment_invoice(user_id, package_id, chat_id)
        
    except Exception as e:
        logger.error(f"Error in pay command: {str(e)}")
        await message.answer("❌ Ошибка при создании счета")

@dp.pre_checkout_query()
async def pre_checkout_query(pre_checkout: PreCheckoutQuery):
    """
    Предварительная проверка перед оплатой
    """
    try:
        logger.info(f"Pre-checkout query: {pre_checkout.invoice_payload}")
        
        # Здесь можно добавить дополнительные проверки
        # Например, проверить доступность тарифа
        
        await pre_checkout.answer(ok=True)
        
    except Exception as e:
        logger.error(f"Error in pre-checkout: {str(e)}")
        await pre_checkout.answer(
            ok=False, 
            error_message="Произошла ошибка. Попробуйте позже."
        )

@dp.message(lambda message: message.successful_payment)
async def successful_payment(message: types.Message):
    """
    Обработка успешной оплаты
    """
    try:
        payment: SuccessfulPayment = message.successful_payment
        payload = payment.invoice_payload
        
        logger.info(f"Successful payment: {payload}")
        
        # Парсим payload: package_id_user_id
        if payload.startswith("package_"):
            parts = payload.split("_")
            if len(parts) >= 3:
                package_id = parts[1]
                user_id = int(parts[2])
                
                # Уведомляем backend о успешной оплате
                payment_data = {
                    "user_id": str(user_id),
                    "package_id": package_id,
                    "telegram_charge_id": payment.telegram_payment_charge_id,
                    "provider_charge_id": payment.provider_payment_charge_id,
                    "amount": payment.total_amount / 100,  # Конвертируем из копеек
                    "currency": payment.currency,
                    "payload": payload
                }
                
                # Вызываем API backend для сохранения платежа
                result = await marketplace_bot.call_backend_api(
                    "/packages/confirm-payment", 
                    "POST", 
                    payment_data
                )
                
                if result:
                    # Успешная оплата
                    await message.answer(
                        "✅ <b>Оплата прошла успешно!</b>\n\n"
                        f"💎 Тариф активирован\n"
                        f"💰 Сумма: {payment.total_amount / 100} {payment.currency}\n\n"
                        "Теперь вы можете создать объявление в приложении! 🚀",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(
                                text="📱 Открыть приложение",
                                web_app=WebAppInfo(url=MINIAPP_URL)
                            )]
                        ]),
                        parse_mode="HTML"
                    )
                else:
                    # Ошибка на backend
                    await message.answer(
                        "⚠️ Оплата получена, но возникла ошибка активации.\n"
                        "Обратитесь в поддержку: @support"
                    )
                
                logger.info(f"Payment processed for user {user_id}, package {package_id}")
                
        else:
            logger.error(f"Invalid payment payload: {payload}")
            await message.answer("❌ Ошибка обработки платежа. Обратитесь в поддержку.")
            
    except Exception as e:
        logger.error(f"Error processing successful payment: {str(e)}")
        await message.answer(
            "❌ Произошла ошибка при обработке платежа.\n"
            "Обратитесь в поддержку: @support"
        )

async def main():
    """Основная функция для запуска бота"""
    try:
        # Удаляем webhook перед запуском polling
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("🤖 Telegram Bot запущен в режиме polling")
        logger.info(f"📱 Mini App URL: {MINIAPP_URL}")
        
        # Запускаем polling
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    # Проверяем наличие необходимых переменных
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        exit(1)
    
    if not PAYMENT_PROVIDER_TOKEN:
        print("❌ TELEGRAM_PAYMENTS_TOKEN не найден в переменных окружения")
        exit(1)
    
    print("🚀 Запуск Telegram бота...")
    print(f"📱 Mini App URL: {MINIAPP_URL}")
    
    # Запускаем бота
    asyncio.run(main())