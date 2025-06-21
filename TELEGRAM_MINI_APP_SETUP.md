# 🤖 Настройка Telegram Mini App

## 📋 Пошаговая инструкция для настройки бота

### 1. Создание Telegram Bot

1. Откройте [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте команду `/newbot`
3. Введите название вашего бота (например: "Marketplace Bot")
4. Введите username бота (например: "marketplace_demo_bot")
5. Сохраните полученный **BOT_TOKEN**

### 2. Настройка Mini App

1. В чате с [@BotFather](https://t.me/botfather) отправьте `/newapp`
2. Выберите вашего бота из списка
3. Введите название Mini App (например: "Marketplace")
4. Введите описание приложения
5. Загрузите иконку (512x512 px, JPG/PNG)
6. Введите URL вашего приложения: `https://ваш-домен.com`

### 3. Получение ссылки для авторизации

После создания Mini App вы получите ссылку вида:
```
https://t.me/ваш_бот_username/название_app
```

Пример: `https://t.me/marketplace_demo_bot/marketplace`

### 4. Настройка переменных окружения

Добавьте в файл `/app/backend/.env`:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=ваш_токен_бота
TELEGRAM_PAYMENT_TOKEN=ваш_токен_платежей  # Если нужны платежи
TELEGRAM_MODERATOR_CHAT_ID=ваш_чат_id      # Для уведомлений модератора

# Admin Configuration  
ADMIN_USERNAME=admin
ADMIN_PASSWORD=ваш_безопасный_пароль

# App Configuration
APP_URL=https://ваш-домен.com
```

### 5. Настройка Domain в Telegram

1. В [@BotFather](https://t.me/botfather) отправьте `/myapps`
2. Выберите ваше приложение
3. Нажмите "Edit App"
4. Обновите URL на ваш production домен

### 6. Тестирование

1. Откройте ссылку Mini App в Telegram
2. Приложение должно автоматически получить данные пользователя
3. Проверьте создание постов (требуется авторизация)

### 7. Дополнительные настройки

#### Payments (опционально)
Для настройки платежей:
1. Получите Payment Token от провайдера (Stripe, ЮKassa и др.)
2. Настройте в [@BotFather](https://t.me/botfather) через `/mybots` → Payments

#### Webhooks для модерации (опционально)
Для получения уведомлений о постах:
1. Настройте webhook URL: `https://ваш-домен.com/webhook`
2. Укажите TELEGRAM_MODERATOR_CHAT_ID в .env

### 🔐 Безопасность

1. **Всегда проверяйте initData** от Telegram WebApp
2. **Используйте HTTPS** для production
3. **Не передавайте секретные токены** на frontend
4. **Валидируйте данные пользователя** на backend

### 📱 Оптимизация для Telegram

Приложение уже оптимизировано:
- ✅ Один API запрос для всех справочных данных
- ✅ Пагинация постов (20 на страницу)
- ✅ Индексы базы данных для быстрых запросов
- ✅ Сжатые ответы API (только нужные поля)
- ✅ Кэширование статических данных

### 🚀 Production Checklist

- [ ] Создан Telegram Bot
- [ ] Настроено Mini App
- [ ] Обновлены переменные окружения
- [ ] Настроен production домен
- [ ] Протестирована авторизация
- [ ] Настроены платежи (если нужно)
- [ ] Настроены уведомления модератора

### 📞 Поддержка

При возникновении проблем проверьте:
1. Правильность URL в настройках Mini App
2. Наличие HTTPS сертификата
3. Корректность токенов в .env файле
4. Логи приложения в browser developer tools

---

## 🔗 Полезные ссылки

- [Telegram Mini Apps Documentation](https://core.telegram.org/bots/webapps)
- [BotFather Commands](https://core.telegram.org/bots#6-botfather)
- [Telegram Payments](https://core.telegram.org/bots/payments)