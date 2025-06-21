# 🔐 Справка по Telegram авторизации

## 📊 Текущая реализация авторизации

### Frontend (React)
- **Местоположение**: `/app/frontend/src/App.js` (строки 52-81)
- **Метод**: Telegram WebApp API (`window.Telegram.WebApp`)
- **Данные**: Получение пользователя из `tg.initDataUnsafe.user`

### Backend API Endpoints
- **Создание/обновление пользователя**: `POST /api/users/`
- **Получение пользователя**: `GET /api/users/{user_id}`
- **Статистика пользователя**: `GET /api/users/{user_id}/stats`

## 🌐 URL для тестирования авторизации

### 1. Основное приложение
```
https://51d971f9-1e69-4e09-9727-e45dadcdbabe.preview.emergentagent.com
```

### 2. API Endpoints для тестирования

#### Health Check
```bash
curl https://51d971f9-1e69-4e09-9727-e45dadcdbabe.preview.emergentagent.com/api/health
```

#### Создание тестового пользователя
```bash
curl -X POST \
  https://51d971f9-1e69-4e09-9727-e45dadcdbabe.preview.emergentagent.com/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": 123456789,
    "first_name": "Test",
    "last_name": "User",
    "username": "testuser",
    "language_code": "ru"
  }'
```

#### Получение пользователя
```bash
curl https://51d971f9-1e69-4e09-9727-e45dadcdbabe.preview.emergentagent.com/api/users/{user_id}
```

## 🔒 Проблемы текущей авторизации

### ❌ Небезопасная реализация
1. **initDataUnsafe не проверяется** - данные могут быть подделаны
2. **Нет валидации hash** - не проверяется подпись Telegram
3. **Отсутствует backend аутентификация** - пользователь создается без проверки

### ✅ Что нужно исправить
1. Добавить проверку `initData` с hash валидацией
2. Создать middleware для проверки авторизации
3. Добавить JWT токены для сессий
4. Валидировать все запросы на backend

## 🛠️ Рекомендуемые улучшения

### 1. Безопасная проверка initData
```python
# Добавить в backend
import hmac
import hashlib
from urllib.parse import unquote, parse_qsl

def validate_telegram_data(init_data: str, bot_token: str) -> dict:
    """Проверка подлинности данных от Telegram WebApp"""
    parsed_data = dict(parse_qsl(unquote(init_data)))
    
    # Извлекаем hash
    received_hash = parsed_data.pop('hash', '')
    
    # Создаем строку для проверки
    data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(parsed_data.items())])
    
    # Создаем секретный ключ
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    
    # Проверяем hash
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    if calculated_hash == received_hash:
        return parsed_data
    else:
        raise ValueError("Invalid Telegram data")
```

### 2. Middleware для авторизации
```python
# Добавить middleware в main.py
from fastapi import Request, HTTPException

async def auth_middleware(request: Request):
    """Middleware для проверки авторизации"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    # Проверка JWT токена или Telegram initData
    # ...
```

## 🧪 Как протестировать авторизацию

### В браузере (симуляция)
1. Откройте Developer Tools (F12)
2. В Console выполните:
```javascript
// Симуляция Telegram WebApp
window.Telegram = {
  WebApp: {
    ready: () => console.log('Telegram WebApp ready'),
    initDataUnsafe: {
      user: {
        id: 123456789,
        first_name: "Test",
        last_name: "User",
        username: "testuser",
        language_code: "ru"
      }
    },
    colorScheme: "light",
    close: () => console.log('App closed')
  }
};

// Перезагрузите страницу
location.reload();
```

### В реальном Telegram Bot
1. Создайте бота через [@BotFather](https://t.me/botfather)
2. Создайте Mini App с URL: `https://51d971f9-1e69-4e09-9727-e45dadcdbabe.preview.emergentagent.com`
3. Откройте приложение через ссылку: `https://t.me/your_bot/your_app`

## 🔧 Статус функций авторизации

### ✅ Работает
- [x] Получение данных пользователя из Telegram WebApp
- [x] Отображение статуса авторизации в UI
- [x] Ограничение функций для неавторизованных
- [x] API для создания/получения пользователей

### ❌ Требует исправления
- [ ] Проверка подлинности initData
- [ ] JWT токены для сессий
- [ ] Middleware авторизации
- [ ] Безопасная передача данных пользователя

## 🚨 Критические замечания

1. **Данные пользователя не проверяются** - любой может подделать telegram_id
2. **Нет защиты API** - endpoints доступны без авторизации
3. **initDataUnsafe** - используются небезопасные данные
4. **Отсутствует валидация** - нет проверки hash от Telegram

## 📝 План действий для исправления

1. ✅ Создать endpoint для валидации Telegram данных
2. ✅ Добавить JWT токены
3. ✅ Создать middleware для проверки авторизации
4. ✅ Обновить frontend для безопасной авторизации
5. ✅ Протестировать с реальным Telegram Bot

Хотите, чтобы я реализовал эти улучшения?