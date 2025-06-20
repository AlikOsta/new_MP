import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from core.config import settings

# Initialize Bot
bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_command(message: types.Message):
    """Handle /start command"""
    web_app = WebAppInfo(url="https://your-domain.com")  # Replace with your domain
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏪 Открыть магазин", web_app=web_app)]
    ])
    
    await message.answer(
        "Добро пожаловать в Telegram Mini App - платформу частных объявлений!\n\n"
        "🔍 Ищите работу и услуги\n"
        "💼 Размещайте объявления\n"
        "💳 Безопасные платежи\n\n"
        "Нажмите кнопку ниже, чтобы начать:",
        reply_markup=keyboard
    )

@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    """Handle pre-checkout queries for payments"""
    await pre_checkout_query.answer(ok=True)

@dp.message(lambda message: message.successful_payment)
async def successful_payment(message: types.Message):
    """Handle successful payments"""
    payment_info = message.successful_payment
    
    # Here you would update your database with payment information
    # and activate the post
    
    await message.answer(
        f"✅ Платеж успешно выполнен!\n"
        f"💰 Сумма: {payment_info.total_amount // 100} {payment_info.currency}\n"
        f"📄 Ваше объявление будет активировано в течение нескольких минут."
    )

async def start_bot():
    """Start the bot with webhook or polling"""
    if settings.webhook_url:
        await bot.set_webhook(url=f"{settings.webhook_url}/webhook")
        print(f"Webhook set to: {settings.webhook_url}/webhook")
    else:
        await dp.start_polling(bot)
        print("Bot started with polling")

async def stop_bot():
    """Stop the bot"""
    await bot.session.close()

# Webhook endpoint
async def webhook_handler(request):
    """Handle webhook requests"""
    update = types.Update.model_validate(await request.json())
    await dp.process_update(update, bot=bot)
    return {"ok": True}