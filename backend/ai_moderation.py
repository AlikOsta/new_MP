import asyncio
import httpx
import json
import os
from datetime import datetime
from typing import Dict, Any, Tuple

class MistralModerator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.mistral.ai/v1"
        self.model = "mistral-small-latest"
        
    async def moderate_post(self, title: str, description: str, post_type: str = "general") -> Tuple[str, float, str]:
        """
        Модерирует объявление через Mistral AI
        
        Returns:
            Tuple[decision, confidence, reason]
            decision: "approved" | "rejected" 
            confidence: float 0.0-1.0
            reason: string объяснение решения
        """
        
        prompt = self._build_moderation_prompt(title, description, post_type)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "Ты модератор объявлений на платформе частных объявлений. Твоя задача - определить, соответствует ли объявление правилам платформы."
                            },
                            {
                                "role": "user", 
                                "content": prompt
                            }
                        ],
                        "temperature": 0.1,
                        "max_tokens": 200
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result["choices"][0]["message"]["content"]
                    return self._parse_ai_response(ai_response)
                else:
                    print(f"Mistral API error: {response.status_code} - {response.text}")
                    return "approved", 0.5, "ИИ модерация недоступна, пропускаем"
                    
        except Exception as e:
            print(f"Error in AI moderation: {str(e)}")
            return "approved", 0.5, f"Ошибка ИИ модерации: {str(e)}"
    
    def _build_moderation_prompt(self, title: str, description: str, post_type: str) -> str:
        """Создает промпт для модерации"""
        
        rules = """
ПРАВИЛА МОДЕРАЦИИ:

ЗАПРЕЩЕНО:
❌ Продажа запрещенных товаров (наркотики, оружие, алкоголь, лекарства)
❌ Мошеннические схемы и финансовые пирамиды  
❌ Контент 18+ и эротические услуги
❌ Азартные игры и букмекерские услуги
❌ Оскорбления, угрозы, дискриминация
❌ Спам, реклама других платформ
❌ Продажа аккаунтов, документов, дипломов
❌ Нарушение авторских прав
❌ Контактные данные в тексте (телефоны, email, соцсети)

РАЗРЕШЕНО:
✅ Поиск и предложение работы
✅ Бытовые и профессиональные услуги  
✅ Репетиторство и обучение
✅ Ремонт и строительство
✅ IT услуги и разработка
✅ Дизайн и творчество
✅ Доставка и перевозки
✅ Юридические услуги

ДОПОЛНИТЕЛЬНЫЕ ПРОВЕРКИ:
⚠️ Подозрительно низкие/высокие цены
⚠️ Слишком общие описания без деталей
⚠️ Грамматические ошибки могут указывать на мошенничество
⚠️ Требование предоплаты без гарантий
"""

        prompt = f"""
{rules}

АНАЛИЗИРУЙ ОБЪЯВЛЕНИЕ:
Тип: {post_type}
Название: "{title}"
Описание: "{description}"

ВЕРНИ ОТВЕТ В ФОРМАТЕ JSON:
{{
    "decision": "approved" или "rejected",
    "confidence": 0.95,
    "reason": "Краткое объяснение решения",
    "violations": ["список нарушений если есть"]
}}

ВАЖНО: Если есть сомнения - лучше отклонить и отправить на ручную модерацию.
"""
        return prompt
    
    def _parse_ai_response(self, ai_response: str) -> Tuple[str, float, str]:
        """Парсит ответ ИИ"""
        try:
            # Пытаемся извлечь JSON из ответа
            start = ai_response.find('{')
            end = ai_response.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = ai_response[start:end]
                result = json.loads(json_str)
                
                decision = result.get("decision", "approved")
                confidence = float(result.get("confidence", 0.5))
                reason = result.get("reason", "ИИ модерация завершена")
                violations = result.get("violations", [])
                
                if violations:
                    reason += f" Нарушения: {', '.join(violations)}"
                
                return decision, confidence, reason
            else:
                # Если JSON не найден, анализируем текст
                if any(word in ai_response.lower() for word in ["reject", "отклон", "запрещ", "нарушен"]):
                    return "rejected", 0.8, "ИИ обнаружил потенциальные нарушения"
                else:
                    return "approved", 0.7, "ИИ одобрил объявление"
                    
        except Exception as e:
            print(f"Error parsing AI response: {str(e)}")
            return "approved", 0.5, f"Ошибка парсинга ответа ИИ: {str(e)}"


class TelegramNotifier:
    def __init__(self, bot_token: str, moderator_chat_id: str):
        self.bot_token = bot_token
        self.moderator_chat_id = moderator_chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        
    async def send_moderation_request(self, post_data: Dict[str, Any], ai_result: Dict[str, Any] = None) -> bool:
        """Отправляет запрос на модерацию в Telegram"""
        
        try:
            message = self._format_moderation_message(post_data, ai_result)
            keyboard = self._create_moderation_keyboard(post_data["id"])
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.moderator_chat_id,
                        "text": message,
                        "reply_markup": keyboard,
                        "parse_mode": "HTML"
                    }
                )
                
                return response.status_code == 200
                
        except Exception as e:
            print(f"Error sending Telegram notification: {str(e)}")
            return False
    
    def _format_moderation_message(self, post_data: Dict[str, Any], ai_result: Dict[str, Any] = None) -> str:
        """Форматирует сообщение для модератора"""
        
        post_type_name = "Работа" if post_data.get("post_type") == "job" else "Услуга"
        price_info = f"{post_data.get('price', 'Не указана')} ₽" if post_data.get("price") else "Цена не указана"
        
        message = f"""
🔍 <b>НОВОЕ ОБЪЯВЛЕНИЕ НА МОДЕРАЦИИ</b>

📋 <b>Тип:</b> {post_type_name}
📝 <b>Название:</b> {post_data.get('title', 'Без названия')}
💰 <b>Цена:</b> {price_info}

📄 <b>Описание:</b>
{post_data.get('description', 'Описание отсутствует')}

👤 <b>Автор:</b> {post_data.get('author_id', 'Неизвестен')}
🆔 <b>ID поста:</b> {post_data.get('id')}
⏰ <b>Создано:</b> {post_data.get('created_at', 'Неизвестно')}
"""

        if ai_result:
            ai_decision = "✅ Одобрено" if ai_result.get("decision") == "approved" else "❌ Отклонено"
            confidence = ai_result.get("confidence", 0) * 100
            
            message += f"""

🤖 <b>РЕЗУЛЬТАТ ИИ МОДЕРАЦИИ:</b>
{ai_decision} (уверенность: {confidence:.0f}%)
💭 {ai_result.get("reason", "Причина не указана")}
"""

        message += "\n\n<b>Выберите действие:</b>"
        return message
    
    def _create_moderation_keyboard(self, post_id: str) -> Dict[str, Any]:
        """Создает клавиатуру для модерации"""
        
        return {
            "inline_keyboard": [
                [
                    {"text": "✅ Опубликовать", "callback_data": f"approve_{post_id}"},
                    {"text": "❌ Отклонить", "callback_data": f"reject_{post_id}"}
                ],
                [
                    {"text": "📋 Детали поста", "callback_data": f"details_{post_id}"}
                ]
            ]
        }
    
    async def send_status_update(self, post_data: Dict[str, Any], status: str, moderator_username: str = None) -> bool:
        """Отправляет уведомление об изменении статуса"""
        
        try:
            status_text = {
                "approved": "✅ ОПУБЛИКОВАНО",
                "rejected": "❌ ОТКЛОНЕНО", 
                "blocked": "🚫 ЗАБЛОКИРОВАНО"
            }.get(status, status.upper())
            
            moderator_info = f" модератором @{moderator_username}" if moderator_username else ""
            
            message = f"""
{status_text}

📝 <b>Объявление:</b> {post_data.get('title')}
🆔 <b>ID:</b> {post_data.get('id')}
👤 <b>Автор:</b> {post_data.get('author_id')}
⏰ <b>Обработано:</b> {datetime.now().strftime('%H:%M %d.%m.%Y')}{moderator_info}
"""

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.moderator_chat_id,
                        "text": message,
                        "parse_mode": "HTML"
                    }
                )
                
                return response.status_code == 200
                
        except Exception as e:
            print(f"Error sending status update: {str(e)}")
            return False


# Глобальные экземпляры (будут инициализированы в server.py)
mistral_moderator = None
telegram_notifier = None

async def init_moderation_services():
    """Инициализация сервисов модерации"""
    global mistral_moderator, telegram_notifier
    
    mistral_api_key = os.getenv("MISTRAL_API_KEY")
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN") 
    telegram_moderator_chat_id = os.getenv("TELEGRAM_MODERATOR_CHAT_ID")
    
    if mistral_api_key:
        mistral_moderator = MistralModerator(mistral_api_key)
        print("✅ Mistral moderator initialized")
    else:
        print("⚠️ MISTRAL_API_KEY not found, AI moderation disabled")
    
    if telegram_bot_token and telegram_moderator_chat_id:
        telegram_notifier = TelegramNotifier(telegram_bot_token, telegram_moderator_chat_id)
        print("✅ Telegram notifier initialized")
    else:
        print("⚠️ Telegram credentials not found, notifications disabled")

async def moderate_post_content(post_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Главная функция модерации поста
    
    Returns:
        {
            "decision": "approved" | "rejected" | "manual_review",
            "ai_result": {...},
            "should_notify_moderator": bool,
            "final_status": int
        }
    """
    
    result = {
        "decision": "approved",
        "ai_result": None,
        "should_notify_moderator": False,
        "final_status": 4  # Опубликовано
    }
    
    # ИИ модерация
    if mistral_moderator:
        try:
            ai_decision, ai_confidence, ai_reason = await mistral_moderator.moderate_post(
                post_data.get("title", ""),
                post_data.get("description", ""),
                post_data.get("post_type", "general")
            )
            
            result["ai_result"] = {
                "decision": ai_decision,
                "confidence": ai_confidence,
                "reason": ai_reason,
                "moderated_at": datetime.now().isoformat()
            }
            
            # Если ИИ отклонил с высокой уверенностью
            if ai_decision == "rejected" and ai_confidence > 0.8:
                result["decision"] = "rejected"
                result["final_status"] = 5  # Заблокировано
                return result
            
            # Если ИИ не уверен или включена только ручная модерация
            # (проверяем настройки)
            
        except Exception as e:
            print(f"AI moderation failed: {str(e)}")
    
    # Проверяем настройки модерации из базы данных
    # Если автомодерация выключена или ИИ не уверен - отправляем модератору
    result["decision"] = "manual_review"
    result["should_notify_moderator"] = True
    result["final_status"] = 3  # Проверено (ждет ручной модерации)
    
    return result