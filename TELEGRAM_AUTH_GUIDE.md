# 🔐 Справка по Telegram авторизации

## 🎉 ✅ НОВАЯ БЕЗОПАСНАЯ АВТОРИЗАЦИЯ РЕАЛИЗОВАНА!

### 🔒 Что исправлено:
1. ✅ **Безопасная проверка initData** - валидация hash от Telegram
2. ✅ **JWT токены** - для безопасных сессий 
3. ✅ **Middleware авторизации** - защита API endpoints
4. ✅ **Проверка временных меток** - данные не старше 24 часов

## 🌐 URL для тестирования НОВОЙ авторизации

### 🔥 Основное приложение
```
https://958e1ad6-00a3-4c3e-a8b5-fdd4fba26a4a.preview.emergentagent.com
```

### 🔑 Новые Auth Endpoints

#### 1. Авторизация через Telegram (POST)
```bash
curl -X POST \
  https://958e1ad6-00a3-4c3e-a8b5-fdd4fba26a4a.preview.emergentagent.com/api/auth/telegram \
  -H "Content-Type: application/json" \
  -d '{
    "init_data": "query_id=AAE...&user=%7B%22id%22%3A123456789..."
  }'
```
**Ответ**: JWT token + данные пользователя

#### 2. Проверка авторизации (GET)
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://958e1ad6-00a3-4c3e-a8b5-fdd4fba26a4a.preview.emergentagent.com/api/auth/verify
```

#### 3. Получение текущего пользователя (GET)
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://958e1ad6-00a3-4c3e-a8b5-fdd4fba26a4a.preview.emergentagent.com/api/auth/me
```

#### 4. Выход (POST)
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://958e1ad6-00a3-4c3e-a8b5-fdd4fba26a4a.preview.emergentagent.com/api/auth/logout
```

### 🧪 Тестирование в браузере

#### В Developer Console:
```javascript
// 1. Получить initData из Telegram WebApp
const initData = window.Telegram.WebApp.initData;

// 2. Авторизоваться
fetch('https://958e1ad6-00a3-4c3e-a8b5-fdd4fba26a4a.preview.emergentagent.com/api/auth/telegram', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({init_data: initData})
})
.then(r => r.json())
.then(data => {
  console.log('Auth success:', data);
  localStorage.setItem('auth_token', data.access_token);
});

// 3. Проверить авторизацию
const token = localStorage.getItem('auth_token');
fetch('https://958e1ad6-00a3-4c3e-a8b5-fdd4fba26a4a.preview.emergentagent.com/api/auth/verify', {
  headers: {'Authorization': `Bearer ${token}`}
})
.then(r => r.json())
.then(data => console.log('User:', data));
```

### 🚨 Для тестирования БЕЗ реального Telegram:

**⚠️ Внимание**: Новая авторизация требует валидного initData от Telegram. Для тестирования без Telegram бота используйте **старый endpoint**:

```bash
# Создание тестового пользователя (БЕЗ проверки безопасности)
curl -X POST \
  https://958e1ad6-00a3-4c3e-a8b5-fdd4fba26a4a.preview.emergentagent.com/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": 123456789,
    "first_name": "Test",
    "last_name": "User", 
    "username": "testuser"
  }'
```

## 🔧 Статус новой авторизации

### ✅ Реализовано
- [x] **Валидация initData** с проверкой hash
- [x] **JWT токены** с истечением через 30 дней
- [x] **Защищенные endpoints** с Authorization header
- [x] **Проверка временных меток** (данные не старше 24ч)
- [x] **Middleware авторизации** для всех защищенных API
- [x] **Автоматическое создание/обновление пользователей**

### 🔄 В процессе обновления
- [ ] **Frontend integration** - обновление React компонентов
- [ ] **Защита существующих endpoints** - posts, favorites и др.
- [ ] **Обработка ошибок авторизации** в UI

## 🎯 Как протестировать с реальным Telegram Bot

### 1. Создайте бота:
1. Откройте [@BotFather](https://t.me/botfather)
2. `/newbot` → название → username
3. Сохраните **BOT_TOKEN**: `7554067474:AAG75CqnZSiqKiWgpZ4zX6hNW_e6f9uZn1g`

### 2. Создайте Mini App:
1. В [@BotFather](https://t.me/botfather): `/newapp`
2. Выберите вашего бота
3. URL: `https://958e1ad6-00a3-4c3e-a8b5-fdd4fba26a4a.preview.emergentagent.com`
4. Получите ссылку: `https://t.me/your_bot/your_app`

### 3. Тестируйте авторизацию:
1. Откройте Mini App в Telegram
2. Приложение автоматически получит валидный `initData`
3. Сделает запрос к `/api/auth/telegram`
4. Получит JWT token для дальнейших запросов

## 🔐 Безопасность

### ✅ Что теперь защищено:
1. **Hash валидация** - данные от Telegram не могут быть подделаны
2. **Временные метки** - initData должны быть свежими (< 24ч)
3. **JWT токены** - безопасные сессии с истечением
4. **Authorization headers** - все защищенные API требуют токен

### 🚨 Настройте для продакшна:
1. Измените `SECRET_KEY` в .env на случайную строку
2. Настройте HTTPS сертификат  
3. Обновите URL в Telegram Bot настройках
4. Включите логирование попыток авторизации

**Готово к тестированию! 🚀**