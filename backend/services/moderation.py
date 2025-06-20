import asyncio
import httpx
from typing import Dict, Any
from core.config import settings
from core.database import get_database

class ModerationService:
    def __init__(self):
        self.api_key = settings.mistral_api_key
        self.api_url = "https://api.mistral.ai/v1/chat/completions"
        
    async def moderate_content(self, title: str, description: str) -> Dict[str, Any]:
        """
        Moderate post content using Mistral AI
        Returns: {
            "is_safe": bool,
            "reason": str,
            "confidence": float
        }
        """
        if not self.api_key:
            return {"is_safe": True, "reason": "Moderation disabled", "confidence": 0.0}
        
        content = f"Title: {title}\nDescription: {description}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "mistral-moderation-latest",
            "messages": [
                {
                    "role": "user",
                    "content": f"Please moderate this content for harmful, inappropriate, or spam content:\n\n{content}"
                }
            ]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    choice = result.get("choices", [{}])[0]
                    message = choice.get("message", {}).get("content", "")
                    
                    # Simple parsing - in production you'd want more sophisticated parsing
                    is_safe = "safe" in message.lower() or "appropriate" in message.lower()
                    
                    return {
                        "is_safe": is_safe,
                        "reason": message,
                        "confidence": 0.8 if is_safe else 0.9
                    }
                else:
                    return {"is_safe": True, "reason": "Moderation service unavailable", "confidence": 0.0}
                    
        except Exception as e:
            print(f"Moderation error: {e}")
            return {"is_safe": True, "reason": "Moderation error", "confidence": 0.0}

moderation_service = ModerationService()

async def moderate_post_background(post_id: str):
    """Background task to moderate post content"""
    try:
        db = await get_database()
        post = await db.posts.find_one({"_id": post_id})
        
        if not post:
            return
        
        result = await moderation_service.moderate_content(
            post["title"],
            post["description"]
        )
        
        if not result["is_safe"]:
            # Block the post
            await db.posts.update_one(
                {"_id": post_id},
                {"$set": {"status": 4}}  # BLOCKED status
            )
            print(f"Post {post_id} blocked by moderation: {result['reason']}")
        else:
            # Set to moderation passed - ready for activation
            await db.posts.update_one(
                {"_id": post_id},
                {"$set": {"status": 2}}  # MODERATION status
            )
            print(f"Post {post_id} passed moderation")
            
    except Exception as e:
        print(f"Background moderation error: {e}")