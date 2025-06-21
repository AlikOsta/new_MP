"""
Telegram Bot для Telegram Marketplace Mini App
Использует python-telegram-bot (стабильную библиотеку)
"""

import asyncio
import os
import logging
from typing import Dict, Any
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, LabeledPrice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, filters, ContextTypes
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
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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

# Инициализируем бота
marketplace_bot = TelegramMarketplaceBot()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        keyboard = InlineKeyboardMarkup([
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
        
        await update.message.reply_text(
            text=welcome_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        logger.info(f"Start command processed for user {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Error in start command: {str(e)}")
        await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка кнопки помощи"""
    query = update.callback_query
    await query.answer()
    
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
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_start")]
    ])
    
    await query.edit_message_text(
        text=help_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

async def back_to_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Возврат к стартовому сообщению"""
    query = update.callback_query
    await query.answer()
    
    webapp_button = InlineKeyboardButton(
        text="🚀 Открыть Маркетплейс",
        web_app=WebAppInfo(url=MINIAPP_URL)
    )
    
    help_button = InlineKeyboardButton(
        text="❓ Помощь",
        callback_data="help"
    )
    
    keyboard = InlineKeyboardMarkup([
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
    
    await query.edit_message_text(
        text=welcome_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

async def pay_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Команда для тестирования платежей (только для разработки)
    Использование: /pay package_id
    """
    try:
        args = context.args
        if not args:
            await update.message.reply_text("Использование: /pay package_id")
            return
        
        package_id = args[0]
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Получаем информацию о тарифе
        package_info = await marketplace_bot.get_package_info(package_id)
        
        if not package_info:
            await update.message.reply_text("❌ Тариф не найден")
            return
        
        # Создаем payload для связки с backend
        payload = f"package_{package_id}_{user_id}"
        
        # Цена в копейках (для RUB)
        price_kopecks = int(package_info["price"] * 100)
        
        # Отправляем инвойс
        await context.bot.send_invoice(
            chat_id=chat_id,
            title=f"Тариф: {package_info['name_ru']}",
            description=f"Покупка тарифа для публикации объявления\n{package_info.get('features_ru', '')}",
            payload=payload,
            provider_token=marketplace_bot.payment_provider_token,
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
        logger.error(f"Error in pay command: {str(e)}")
        await update.message.reply_text("❌ Ошибка при создании счета")

async def pre_checkout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Предварительная проверка перед оплатой
    """
    query = update.pre_checkout_query
    
    try:
        logger.info(f"Pre-checkout query: {query.invoice_payload}")
        
        # Здесь можно добавить дополнительные проверки
        # Например, проверить доступность тарифа
        
        await query.answer(ok=True)
        
    except Exception as e:
        logger.error(f"Error in pre-checkout: {str(e)}")
        await query.answer(
            ok=False, 
            error_message="Произошла ошибка. Попробуйте позже."
        )

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработка успешной оплаты
    """
    try:
        payment = update.message.successful_payment
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
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="📱 Открыть приложение",
                            web_app=WebAppInfo(url=MINIAPP_URL)
                        )]
                    ])
                    
                    await update.message.reply_text(
                        "✅ <b>Оплата прошла успешно!</b>\n\n"
                        f"💎 Тариф активирован\n"
                        f"💰 Сумма: {payment.total_amount / 100} {payment.currency}\n\n"
                        "Теперь вы можете создать объявление в приложении! 🚀",
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                else:
                    # Ошибка на backend
                    await update.message.reply_text(
                        "⚠️ Оплата получена, но возникла ошибка активации.\n"
                        "Обратитесь в поддержку: @support"
                    )
                
                logger.info(f"Payment processed for user {user_id}, package {package_id}")
                
        else:
            logger.error(f"Invalid payment payload: {payload}")
            await update.message.reply_text("❌ Ошибка обработки платежа. Обратитесь в поддержку.")
            
    except Exception as e:
        logger.error(f"Error processing successful payment: {str(e)}")
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке платежа.\n"
            "Обратитесь в поддержку: @support"
        )

def main():
    """Основная функция для запуска бота"""
    
    # Проверяем наличие необходимых переменных
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        exit(1)
    
    if not PAYMENT_PROVIDER_TOKEN:
        print("❌ TELEGRAM_PAYMENTS_TOKEN не найден в переменных окружения")
        exit(1)
    
    print("🚀 Запуск Telegram бота...")
    print(f"📱 Mini App URL: {MINIAPP_URL}")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("pay", pay_command))
    application.add_handler(CallbackQueryHandler(help_callback, pattern="^help$"))
    application.add_handler(CallbackQueryHandler(back_to_start_callback, pattern="^back_to_start$"))
    application.add_handler(PreCheckoutQueryHandler(pre_checkout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    
    # Запускаем бота
    logger.info("🤖 Telegram Bot запущен в режиме polling")
    logger.info(f"📱 Mini App URL: {MINIAPP_URL}")
    
    # Запуск polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()