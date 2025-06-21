"""
Webhook router - handles Telegram bot webhook
"""
from fastapi import APIRouter, Request
import httpx
from database import db
from datetime import datetime
from services.moderation_service import ModerationService
from ai_moderation import telegram_notifier

router = APIRouter(tags=["webhook"])

@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Telegram bot webhook endpoint"""
    try:
        update = await request.json()
        
        # Handle callback query (moderator button clicks)
        if "callback_query" in update:
            callback = update["callback_query"]
            callback_data = callback.get("data", "")
            chat_id = callback["message"]["chat"]["id"]
            message_id = callback["message"]["message_id"]
            
            # Extract action and post ID
            if "_" in callback_data:
                action, post_id = callback_data.split("_", 1)
                
                if action in ["approve", "reject"]:
                    # Handle moderation decision
                    success = await ModerationService.handle_moderation_decision(
                        action, post_id, callback["from"]
                    )
                    
                    if success:
                        # Update Telegram message
                        await update_telegram_message(chat_id, message_id, action, post_id)
        
        return {"ok": True}
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return {"ok": True}  # Always return success for Telegram

async def update_telegram_message(chat_id: str, message_id: int, action: str, post_id: str):
    """Update Telegram message after moderation decision"""
    if not telegram_notifier:
        return
    
    try:
        action_text = "✅ ОПУБЛИКОВАНО" if action == "approve" else "❌ ОТКЛОНЕНО"
        new_text = f"{action_text}\n\nОбъявление {post_id} обработано."
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                f"{telegram_notifier.base_url}/editMessageText",
                json={
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "text": new_text,
                    "parse_mode": "HTML"
                }
            )
    except Exception as e:
        print(f"Error updating Telegram message: {str(e)}")