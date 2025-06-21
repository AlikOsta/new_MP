"""
Statistics service - handles analytics and reporting
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
from database import db

class StatsService:
    """Service for handling statistics and analytics"""
    
    @staticmethod
    async def get_admin_stats() -> Dict[str, Any]:
        """Get comprehensive admin statistics"""
        try:
            now = datetime.now().isoformat()
            
            # Basic counts
            total_posts = await db.fetchone("SELECT COUNT(*) as count FROM posts")
            total_users = await db.fetchone("SELECT COUNT(*) as count FROM users")
            active_posts = await db.fetchone("SELECT COUNT(*) as count FROM posts WHERE status = 4")
            pending_posts = await db.fetchone("SELECT COUNT(*) as count FROM posts WHERE status IN (2, 3)")
            
            # Posts by type
            job_posts = await db.fetchone("SELECT COUNT(*) as count FROM posts WHERE post_type = 'job'")
            service_posts = await db.fetchone("SELECT COUNT(*) as count FROM posts WHERE post_type = 'service'")
            
            # Posts by status
            status_counts = await db.fetchall("""
                SELECT status, COUNT(*) as count 
                FROM posts 
                GROUP BY status
            """)
            
            # Recent activity (last 7 days)
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            recent_posts = await db.fetchone(
                "SELECT COUNT(*) as count FROM posts WHERE created_at >= ?", 
                [week_ago]
            )
            recent_users = await db.fetchone(
                "SELECT COUNT(*) as count FROM users WHERE created_at >= ?", 
                [week_ago]
            )
            
            # Premium vs Free posts
            premium_posts = await db.fetchone("SELECT COUNT(*) as count FROM posts WHERE is_premium = 1")
            free_posts = await db.fetchone("SELECT COUNT(*) as count FROM posts WHERE is_premium = 0")
            
            return {
                "overview": {
                    "total_posts": total_posts["count"] if total_posts else 0,
                    "total_users": total_users["count"] if total_users else 0,
                    "active_posts": active_posts["count"] if active_posts else 0,
                    "pending_posts": pending_posts["count"] if pending_posts else 0
                },
                "posts_by_type": {
                    "jobs": job_posts["count"] if job_posts else 0,
                    "services": service_posts["count"] if service_posts else 0
                },
                "posts_by_status": {
                    row["status"]: row["count"] for row in status_counts
                },
                "recent_activity": {
                    "posts_last_week": recent_posts["count"] if recent_posts else 0,
                    "users_last_week": recent_users["count"] if recent_users else 0
                },
                "premium_breakdown": {
                    "premium_posts": premium_posts["count"] if premium_posts else 0,
                    "free_posts": free_posts["count"] if free_posts else 0
                }
            }
            
        except Exception as e:
            print(f"Error getting admin stats: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    async def get_moderation_stats() -> Dict[str, Any]:
        """Get moderation statistics"""
        try:
            now = datetime.now().isoformat()
            
            # Posts ready to expire
            expire_ready = await db.fetchone(
                "SELECT COUNT(*) as count FROM posts WHERE expires_at < ? AND status = 4",
                [now]
            )
            
            # Posts ready to boost
            boost_ready = await db.fetchone(
                "SELECT COUNT(*) as count FROM post_boost_schedule WHERE next_boost_at < ? AND is_active = 1",
                [now]
            )
            
            # AI moderation stats
            ai_approvals = await db.fetchone(
                "SELECT COUNT(*) as count FROM ai_moderation_log WHERE ai_decision = 'approved'"
            )
            ai_rejections = await db.fetchone(
                "SELECT COUNT(*) as count FROM ai_moderation_log WHERE ai_decision = 'rejected'"
            )
            ai_manual_review = await db.fetchone(
                "SELECT COUNT(*) as count FROM ai_moderation_log WHERE ai_decision = 'manual_review'"
            )
            
            return {
                "background_tasks": {
                    "posts_ready_to_expire": expire_ready["count"] if expire_ready else 0,
                    "posts_ready_to_boost": boost_ready["count"] if boost_ready else 0
                },
                "ai_moderation": {
                    "approved": ai_approvals["count"] if ai_approvals else 0,
                    "rejected": ai_rejections["count"] if ai_rejections else 0,
                    "manual_review": ai_manual_review["count"] if ai_manual_review else 0
                }
            }
            
        except Exception as e:
            print(f"Error getting moderation stats: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    async def get_user_stats(user_id: str) -> Dict[str, Any]:
        """Get statistics for a specific user"""
        try:
            # User's posts
            user_posts = await db.fetchall(
                "SELECT status, COUNT(*) as count FROM posts WHERE author_id = ? GROUP BY status",
                [user_id]
            )
            
            # User's favorites
            user_favorites = await db.fetchone(
                "SELECT COUNT(*) as count FROM favorites WHERE user_id = ?",
                [user_id]
            )
            
            # User's views
            user_views = await db.fetchone(
                "SELECT SUM(views_count) as total_views FROM posts WHERE author_id = ?",
                [user_id]
            )
            
            # Check free post availability
            from services.post_service import PostService
            free_post_status = await PostService.check_free_post_availability(user_id)
            
            return {
                "posts_by_status": {
                    row["status"]: row["count"] for row in user_posts
                },
                "favorites_count": user_favorites["count"] if user_favorites else 0,
                "total_views": user_views["total_views"] if user_views and user_views["total_views"] else 0,
                "free_post_available": free_post_status["can_create_free"],
                "next_free_post_at": free_post_status["next_free_at"]
            }
            
        except Exception as e:
            print(f"Error getting user stats: {str(e)}")
            return {"error": str(e)}