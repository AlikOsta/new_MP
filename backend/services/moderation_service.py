"""
Moderation service - handles AI moderation and approval workflows
"""
from datetime import datetime
from typing import Dict, Any, Optional
from database import db
from ai_moderation import moderate_post_content, telegram_notifier

class ModerationService:
    """Service for handling post moderation"""
    
    @staticmethod
    async def moderate_post(post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle AI moderation for a post
        """
        try:
            # Start AI moderation process
            moderation_result = await moderate_post_content(post_data)
            
            # Log AI moderation result
            if moderation_result.get("ai_result"):
                await ModerationService._log_ai_moderation(
                    post_data["id"], 
                    moderation_result["ai_result"]
                )
            
            # Update post status based on moderation result
            final_status = moderation_result.get("final_status", 3)
            await db.update("posts", {
                "status": final_status,
                "ai_moderation_passed": moderation_result["decision"] != "rejected"
            }, "id = ?", [post_data["id"]])
            
            # Send notification to moderator if needed
            if moderation_result.get("should_notify_moderator") and telegram_notifier:
                await telegram_notifier.send_moderation_request(
                    post_data, 
                    moderation_result.get("ai_result")
                )
            
            return {
                "status": final_status,
                "ai_moderation_passed": moderation_result["decision"] != "rejected",
                "moderation_result": moderation_result
            }
            
        except Exception as e:
            print(f"Error in moderation process: {str(e)}")
            # If moderation fails, set status to manual review
            await db.update("posts", {"status": 3}, "id = ?", [post_data["id"]])
            return {
                "status": 3,
                "ai_moderation_passed": False,
                "error": str(e)
            }
    
    @staticmethod
    async def handle_moderation_decision(action: str, post_id: str, moderator_info: Dict[str, Any]) -> bool:
        """
        Handle moderator decision (approve/reject)
        """
        try:
            # Get post
            post = await db.fetchone("SELECT * FROM posts WHERE id = ?", [post_id])
            if not post:
                print(f"Post {post_id} not found")
                return False
            
            # Determine new status
            new_status = 4 if action == "approve" else 5  # Published or Blocked
            
            # Update post
            await db.update("posts", {
                "status": new_status,
                "updated_at": datetime.now().isoformat()
            }, "id = ?", [post_id])
            
            # If post was premium and rejected - handle refund
            if action == "reject" and post.get("is_premium"):
                await ModerationService._handle_refund(post_id, post.get("author_id"))
            
            # Send status update notification
            if telegram_notifier:
                status_text = "approved" if action == "approve" else "rejected"
                moderator_username = moderator_info.get("username", "неизвестен")
                await telegram_notifier.send_status_update(dict(post), status_text, moderator_username)
            
            print(f"Post {post_id} {action}ed by moderator {moderator_info.get('username', 'unknown')}")
            return True
            
        except Exception as e:
            print(f"Error handling moderation decision: {str(e)}")
            return False
    
    @staticmethod
    async def _log_ai_moderation(post_id: str, ai_result: Dict[str, Any]):
        """Log AI moderation result"""
        ai_log_data = {
            "post_id": post_id,
            "ai_decision": ai_result["decision"],
            "ai_confidence": ai_result["confidence"],
            "ai_reason": ai_result["reason"],
            "moderated_at": datetime.now().isoformat()
        }
        await db.insert("ai_moderation_log", ai_log_data)
    
    @staticmethod
    async def _handle_refund(post_id: str, author_id: str):
        """Handle refund for rejected premium post"""
        try:
            # Find package purchase for this post
            purchase = await db.fetchone(
                "SELECT * FROM user_packages WHERE post_id = ? AND payment_status = 'paid'", 
                [post_id]
            )
            
            if purchase:
                # Mark as refunded
                await db.update("user_packages", {
                    "payment_status": "refunded"
                }, "id = ?", [purchase["id"]])
                
                print(f"Refund processed for post {post_id}, user {author_id}, amount {purchase.get('amount', 0)}")
                
                # Here you can add integration with real payment system for refund
                
        except Exception as e:
            print(f"Error processing refund: {str(e)}")