import asyncio
import os
from datetime import datetime, timedelta
from database import db

class BackgroundTasks:
    def __init__(self):
        self.is_running = False
        self.tasks = []
    
    async def start(self):
        """Запуск всех фоновых задач"""
        if self.is_running:
            return
        
        self.is_running = True
        print("🚀 Starting background tasks...")
        
        # Запускаем задачи
        self.tasks = [
            asyncio.create_task(self.expire_old_posts()),
            asyncio.create_task(self.boost_posts()),
            asyncio.create_task(self.cleanup_old_data())
        ]
        
        # Ждем завершения всех задач (никогда не должно произойти)
        await asyncio.gather(*self.tasks, return_exceptions=True)
    
    async def stop(self):
        """Остановка всех фоновых задач"""
        self.is_running = False
        
        for task in self.tasks:
            task.cancel()
        
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        print("🛑 Background tasks stopped")
    
    async def expire_old_posts(self):
        """Перевод истекших объявлений в архив"""
        while self.is_running:
            try:
                now = datetime.now().isoformat()
                
                # Находим объявления с истекшим сроком
                expired_posts = await db.fetchall(
                    """SELECT id, title, author_id FROM posts 
                       WHERE expires_at < ? AND status = 4""",  # Только опубликованные
                    [now]
                )
                
                if expired_posts:
                    print(f"📦 Found {len(expired_posts)} expired posts, moving to archive...")
                    
                    for post in expired_posts:
                        # Переводим в архив
                        await db.update("posts", {
                            "status": 6,  # Архив
                            "updated_at": now
                        }, "id = ?", [post["id"]])
                        
                        # Деактивируем планировщик поднятия
                        await db.update("post_boost_schedule", {
                            "is_active": False
                        }, "post_id = ?", [post["id"]])
                        
                        print(f"  📁 Archived: {post['title']} (ID: {post['id']})")
                
                # Проверяем каждый час
                await asyncio.sleep(3600)  # 1 hour
                
            except Exception as e:
                print(f"❌ Error in expire_old_posts: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def boost_posts(self):
        """Поднятие объявлений в топ"""
        while self.is_running:
            try:
                now = datetime.now()
                
                # Находим объявления готовые к поднятию
                boost_ready = await db.fetchall(
                    """SELECT pbs.*, p.title, p.author_id 
                       FROM post_boost_schedule pbs
                       JOIN posts p ON pbs.post_id = p.id
                       WHERE pbs.next_boost_at <= ? 
                       AND pbs.is_active = 1 
                       AND p.status = 4""",  # Только опубликованные
                    [now.isoformat()]
                )
                
                if boost_ready:
                    print(f"🚀 Found {len(boost_ready)} posts ready for boost...")
                    
                    for boost in boost_ready:
                        post_id = boost["post_id"]
                        
                        # "Поднимаем" пост (обновляем updated_at для сортировки)
                        await db.update("posts", {
                            "updated_at": now.isoformat()
                        }, "id = ?", [post_id])
                        
                        # Обновляем счетчик и планируем следующее поднятие
                        new_boost_count = boost["boost_count"] + 1
                        
                        # Получаем информацию о пакете для интервала поднятия
                        post_info = await db.fetchone(
                            """SELECT p.*, pkg.boost_interval_days, pkg.duration_days
                               FROM posts p
                               LEFT JOIN packages pkg ON p.package_id = pkg.id
                               WHERE p.id = ?""",
                            [post_id]
                        )
                        
                        boost_interval = post_info.get("boost_interval_days", 3)
                        package_duration = post_info.get("duration_days", 7)
                        
                        # Планируем следующее поднятие если пакет еще активен
                        created_at = datetime.fromisoformat(post_info["created_at"])
                        package_expires = created_at + timedelta(days=package_duration)
                        next_boost_time = now + timedelta(days=boost_interval)
                        
                        if next_boost_time < package_expires:
                            # Планируем следующее поднятие
                            await db.update("post_boost_schedule", {
                                "next_boost_at": next_boost_time.isoformat(),
                                "boost_count": new_boost_count
                            }, "id = ?", [boost["id"]])
                            
                            print(f"  🎯 Boosted: {boost['title']} (boost #{new_boost_count})")
                        else:
                            # Пакет истек, деактивируем поднятие
                            await db.update("post_boost_schedule", {
                                "is_active": False,
                                "boost_count": new_boost_count
                            }, "id = ?", [boost["id"]])
                            
                            print(f"  ⏰ Boost expired for: {boost['title']}")
                
                # Проверяем каждые 30 минут
                await asyncio.sleep(1800)  # 30 minutes
                
            except Exception as e:
                print(f"❌ Error in boost_posts: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def cleanup_old_data(self):
        """Очистка старых данных"""
        while self.is_running:
            try:
                # Удаляем старые логи ИИ модерации (старше 30 дней)
                cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
                
                deleted_logs = await db.delete(
                    "ai_moderation_log", 
                    "moderated_at < ?", 
                    [cutoff_date]
                )
                
                if deleted_logs > 0:
                    print(f"🧹 Cleaned up {deleted_logs} old AI moderation logs")
                
                # Удаляем старые записи просмотров (старше 90 дней)
                cutoff_date_views = (datetime.now() - timedelta(days=90)).isoformat()
                
                deleted_views = await db.delete(
                    "post_views",
                    "viewed_at < ?",
                    [cutoff_date_views]
                )
                
                if deleted_views > 0:
                    print(f"🧹 Cleaned up {deleted_views} old post views")
                
                # Деактивируем неактивные планировщики поднятия
                await db.execute(
                    """UPDATE post_boost_schedule SET is_active = 0 
                       WHERE post_id IN (
                           SELECT id FROM posts WHERE status NOT IN (4)
                       )"""
                )
                
                # Проверяем раз в день
                await asyncio.sleep(86400)  # 24 hours
                
            except Exception as e:
                print(f"❌ Error in cleanup_old_data: {str(e)}")
                await asyncio.sleep(3600)  # Wait 1 hour on error

# Глобальный экземпляр
background_tasks = BackgroundTasks()

async def start_background_tasks():
    """Функция для запуска фоновых задач"""
    await background_tasks.start()

async def stop_background_tasks():
    """Функция для остановки фоновых задач"""
    await background_tasks.stop()

# Вспомогательные функции для ручного управления

async def manual_expire_posts():
    """Ручной запуск архивации истекших постов"""
    now = datetime.now().isoformat()
    
    expired_posts = await db.fetchall(
        """SELECT id, title, expires_at FROM posts 
           WHERE expires_at < ? AND status = 4""",
        [now]
    )
    
    count = 0
    for post in expired_posts:
        await db.update("posts", {
            "status": 6,  # Архив
            "updated_at": now
        }, "id = ?", [post["id"]])
        count += 1
    
    return {"expired_count": count, "expired_posts": expired_posts}

async def manual_boost_posts():
    """Ручной запуск поднятия постов"""
    now = datetime.now()
    
    boost_ready = await db.fetchall(
        """SELECT pbs.*, p.title 
           FROM post_boost_schedule pbs
           JOIN posts p ON pbs.post_id = p.id
           WHERE pbs.next_boost_at <= ? 
           AND pbs.is_active = 1 
           AND p.status = 4""",
        [now.isoformat()]
    )
    
    count = 0
    for boost in boost_ready:
        await db.update("posts", {
            "updated_at": now.isoformat()
        }, "id = ?", [boost["post_id"]])
        
        # Планируем следующее поднятие
        next_boost = now + timedelta(days=3)  # Default 3 days
        await db.update("post_boost_schedule", {
            "next_boost_at": next_boost.isoformat(),
            "boost_count": boost["boost_count"] + 1
        }, "id = ?", [boost["id"]])
        
        count += 1
    
    return {"boosted_count": count, "boosted_posts": boost_ready}