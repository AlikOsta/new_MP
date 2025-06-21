# 🤖 Telegram Bot для Marketplace Mini App

## 📋 Описание

Telegram бот для интеграции с Telegram Mini App маркетплейса. Предоставляет следующие функции:

- **Стартовое сообщение** с кнопкой открытия Mini App
- **Обработка платежей** для платных тарифов
- **Интеграция с FastAPI backend** для подтверждения оплаты
- **Поддержка Telegram Payments API**

## 🚀 Быстрый старт

### 1. Настройка переменных окружения

В файле `backend/.env` уже настроены переменные:

```env
TELEGRAM_BOT_TOKEN="7554067474:AAG75CqnZSiqKiWgpZ4zX6hNW_e6f9uZn1g"
TELEGRAM_PAYMENTS_TOKEN="1744374395:TEST:703d48b8cac170d51296"
```

### 2. Запуск бота

```bash
# Из корневой директории проекта
cd /app
python telegram_bot.py

# Или через скрипт
./run_bot.sh
```

### 3. Тестирование

1. Найдите бота в Telegram по токену
2. Отправьте команду `/start`
3. Нажмите кнопку "🚀 Открыть Маркетплейс"
4. Протестируйте создание объявления с платным тарифом

## 📱 Функции бота

### Команды

- `/start` - Показать приветственное сообщение с кнопкой Mini App
- `/pay package_id` - Создать инвойс для оплаты тарифа (для тестирования)
- `/help` - Показать справку (через кнопку)

### Обработка платежей

1. **Создание инвойса** - бот создает Telegram Invoice
2. **Предварительная проверка** - валидация перед оплатой
3. **Подтверждение платежа** - уведомление backend о успешной оплате
4. **Активация тарифа** - backend активирует тариф для пользователя

## 🔧 Архитектура

### Структура проекта

```
/app/
├── telegram_bot.py          # Основной файл бота
├── run_bot.sh              # Скрипт запуска
├── backend/
│   ├── routers/packages.py  # API для платежей
│   └── .env                # Переменные окружения
```

### Взаимодействие с backend

```python
# Создание инвойса
GET /api/categories/all  # Получение информации о тарифах

# Подтверждение платежа
POST /api/packages/confirm-payment
{
  "user_id": "123",
  "package_id": "premium",
  "telegram_charge_id": "xxx",
  "provider_charge_id": "yyy",
  "amount": 100.0,
  "currency": "RUB"
}
```

## 💰 Интеграция платежей

### Telegram Payments API

Бот использует Telegram Payments API для обработки платежей:

1. **Создание Invoice** - `bot.send_invoice()`
2. **Pre-checkout** - валидация перед оплатой
3. **Successful Payment** - обработка успешной оплаты
4. **Backend Integration** - уведомление backend

### Payload структура

```
package_{package_id}_{user_id}
Пример: package_premium_123456
```

### Статусы платежей

- `pending` - Платеж создан, ожидается оплата
- `completed` - Платеж успешно завершен
- `failed` - Платеж не прошел

## 🛠️ Настройка в Telegram

### 1. Создание бота

1. Найдите @BotFather в Telegram
2. Создайте нового бота: `/newbot`
3. Получите токен бота
4. Настройте команды: `/setcommands`

```
start - Открыть маркетплейс
help - Получить помощь
```

### 2. Настройка платежей

1. Подключите провайдера платежей через @BotFather
2. Получите PAYMENT_TOKEN
3. Настройте валюты и лимиты

### 3. Настройка Mini App

1. Создайте Web App через @BotFather: `/newapp`
2. Укажите URL: `https://your-domain.com`
3. Добавьте описание и иконку

## 🔒 Безопасность

### Защита платежей

- Валидация payload перед обработкой
- Проверка суммы и валюты
- Логирование всех транзакций
- Обработка ошибок

### Переменные окружения

```env
# Обязательные
TELEGRAM_BOT_TOKEN="your_bot_token"
TELEGRAM_PAYMENTS_TOKEN="your_payment_token"

# Опциональные
REACT_APP_BACKEND_URL="https://your-domain.com"
```

## 📊 Мониторинг

### Логирование

Бот логирует:
- Все команды пользователей
- Создание инвойсов
- Успешные платежи
- Ошибки и исключения

### Метрики

- Количество запусков `/start`
- Успешные платежи
- Ошибки при обработке
- Время ответа backend

## 🐛 Отладка

### Проверка окружения

```bash
# Проверить переменные
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_PAYMENTS_TOKEN

# Проверить доступность backend
curl https://your-domain.com/api/health
```

### Тестирование платежей

```bash
# Запустить бота
python telegram_bot.py

# В Telegram отправить:
/start
/pay premium  # Тестовый платеж
```

### Логи

```bash
# Смотреть логи бота
tail -f bot.log

# Логи backend
tail -f /var/log/supervisor/backend.*.log
```

## 🔄 Развертывание

### Production

1. Измените тестовый PAYMENT_TOKEN на реальный
2. Настройте webhook вместо polling
3. Добавьте мониторинг и алерты
4. Настройте автоматический перезапуск

### Webhook настройка

```python
# Для production рекомендуется webhook
await bot.set_webhook(
    url="https://your-domain.com/webhook",
    drop_pending_updates=True
)
```

## 📝 Примеры использования

### Создание инвойса

```python
await marketplace_bot.create_payment_invoice(
    user_id=123456,
    package_id="premium",
    chat_id=123456
)
```

### Проверка статуса платежа

```python
# GET /api/packages/user/123456
[
  {
    "id": "xxx",
    "package_id": "premium",
    "payment_status": "completed",
    "amount": 100.0,
    "currency_code": "RUB"
  }
]
```

## 🆘 Поддержка

При возникновении проблем:

1. Проверьте логи бота и backend
2. Убедитесь в правильности переменных окружения
3. Протестируйте API endpoints
4. Проверьте доступность Telegram API

---

**Бот готов к использованию! 🚀**