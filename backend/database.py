import aiosqlite
import json
import os
from datetime import datetime
import uuid

DATABASE_PATH = os.getenv("DATABASE_PATH", "telegram_marketplace.db")

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
    
    async def init_db(self):
        """Initialize database with all required tables and indexes"""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    telegram_id INTEGER UNIQUE,
                    first_name TEXT,
                    last_name TEXT,
                    username TEXT,
                    language TEXT DEFAULT 'ru',
                    theme TEXT DEFAULT 'light',
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            
            # Super rubrics (categories) table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS super_rubrics (
                    id TEXT PRIMARY KEY,
                    name_ru TEXT,
                    name_ua TEXT,
                    icon TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Cities table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cities (
                    id TEXT PRIMARY KEY,
                    name_ru TEXT,
                    name_ua TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Currencies table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS currencies (
                    id TEXT PRIMARY KEY,
                    code TEXT UNIQUE,
                    name_ru TEXT,
                    name_ua TEXT,
                    symbol TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT
                )
            """)
            
            # Posts table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    post_type TEXT,
                    price REAL,
                    currency_id TEXT,
                    city_id TEXT,
                    super_rubric_id TEXT,
                    author_id TEXT,
                    status INTEGER DEFAULT 1,
                    views_count INTEGER DEFAULT 0,
                    is_premium BOOLEAN DEFAULT 0,
                    package_id TEXT,
                    has_photo BOOLEAN DEFAULT 0,
                    has_highlight BOOLEAN DEFAULT 0,
                    has_boost BOOLEAN DEFAULT 0,
                    post_lifetime_days INTEGER DEFAULT 30,
                    expires_at TEXT,
                    ai_moderation_passed BOOLEAN DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (currency_id) REFERENCES currencies (id),
                    FOREIGN KEY (city_id) REFERENCES cities (id),
                    FOREIGN KEY (super_rubric_id) REFERENCES super_rubrics (id),
                    FOREIGN KEY (author_id) REFERENCES users (id),
                    FOREIGN KEY (package_id) REFERENCES packages (id)
                )
            """)
            
            # Packages table (тарифы)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS packages (
                    id TEXT PRIMARY KEY,
                    name_ru TEXT,
                    name_ua TEXT,
                    package_type TEXT,
                    price REAL,
                    currency_id TEXT,
                    duration_days INTEGER,
                    post_lifetime_days INTEGER DEFAULT 30,
                    features_ru TEXT,
                    features_ua TEXT,
                    has_photo BOOLEAN DEFAULT 0,
                    has_highlight BOOLEAN DEFAULT 0,
                    has_boost BOOLEAN DEFAULT 0,
                    boost_interval_days INTEGER,
                    is_active BOOLEAN DEFAULT 1,
                    sort_order INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (currency_id) REFERENCES currencies (id)
                )
            """)
            
            # User packages (покупки тарифов)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_packages (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    package_id TEXT,
                    post_id TEXT,
                    purchased_at TEXT,
                    expires_at TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    payment_status TEXT DEFAULT 'pending',
                    telegram_charge_id TEXT,
                    provider_charge_id TEXT,
                    amount REAL,
                    currency_code TEXT,
                    created_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (package_id) REFERENCES packages (id),
                    FOREIGN KEY (post_id) REFERENCES posts (id)
                )
            """)
            
            # User free posts tracking
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_free_posts (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    created_at TEXT,
                    next_free_post_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Post boost schedule
            await db.execute("""
                CREATE TABLE IF NOT EXISTS post_boost_schedule (
                    id TEXT PRIMARY KEY,
                    post_id TEXT,
                    next_boost_at TEXT,
                    boost_count INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT,
                    FOREIGN KEY (post_id) REFERENCES posts (id)
                )
            """)
            
            # AI moderation log
            await db.execute("""
                CREATE TABLE IF NOT EXISTS ai_moderation_log (
                    id TEXT PRIMARY KEY,
                    post_id TEXT,
                    ai_decision TEXT,
                    ai_confidence REAL,
                    ai_reason TEXT,
                    moderated_at TEXT,
                    FOREIGN KEY (post_id) REFERENCES posts (id)
                )
            """)
            
            # Favorites table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS favorites (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    post_id TEXT,
                    created_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (post_id) REFERENCES posts (id),
                    UNIQUE(user_id, post_id)
                )
            """)
            
            # Post views table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS post_views (
                    id TEXT PRIMARY KEY,
                    post_id TEXT,
                    user_id TEXT,
                    viewed_at TEXT,
                    FOREIGN KEY (post_id) REFERENCES posts (id),
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(post_id, user_id)
                )
            """)
            
            # App settings table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    id TEXT PRIMARY KEY,
                    show_view_counts BOOLEAN DEFAULT 1,
                    telegram_bot_token TEXT,
                    telegram_payment_token TEXT,
                    telegram_moderator_chat_id TEXT,
                    telegram_moderator_username TEXT,
                    mistral_api_key TEXT,
                    app_name TEXT DEFAULT 'Telegram Marketplace',
                    app_description TEXT DEFAULT 'Платформа частных объявлений',
                    free_posts_per_week INTEGER DEFAULT 1,
                    moderation_enabled BOOLEAN DEFAULT 1,
                    ai_moderation_enabled BOOLEAN DEFAULT 1,
                    post_lifetime_days INTEGER DEFAULT 30,
                    updated_at TEXT
                )
            """)
            
            # Create performance indexes
            await self.create_indexes(db)
            
            await db.commit()
            
            # Initialize default data
            await self.init_default_data(db)
    
    async def create_indexes(self, db):
        """Create indexes for better performance"""
        indexes = [
            # Posts table indexes (most critical for performance)
            "CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status)",
            "CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_posts_author_id ON posts(author_id)",
            "CREATE INDEX IF NOT EXISTS idx_posts_type ON posts(post_type)",
            "CREATE INDEX IF NOT EXISTS idx_posts_category ON posts(super_rubric_id)",
            "CREATE INDEX IF NOT EXISTS idx_posts_city ON posts(city_id)",
            "CREATE INDEX IF NOT EXISTS idx_posts_expires_at ON posts(expires_at)",
            "CREATE INDEX IF NOT EXISTS idx_posts_status_type ON posts(status, post_type)",
            "CREATE INDEX IF NOT EXISTS idx_posts_status_created ON posts(status, created_at DESC)",
            
            # Full-text search index for posts
            "CREATE INDEX IF NOT EXISTS idx_posts_title ON posts(title)",
            
            # Users table indexes
            "CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)",
            "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
            
            # Favorites table indexes
            "CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_favorites_post_id ON favorites(post_id)",
            "CREATE INDEX IF NOT EXISTS idx_favorites_created_at ON favorites(created_at)",
            
            # Post views table indexes
            "CREATE INDEX IF NOT EXISTS idx_post_views_post_id ON post_views(post_id)",
            "CREATE INDEX IF NOT EXISTS idx_post_views_user_id ON post_views(user_id)",
            
            # User packages table indexes
            "CREATE INDEX IF NOT EXISTS idx_user_packages_user_id ON user_packages(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_packages_status ON user_packages(payment_status)",
            "CREATE INDEX IF NOT EXISTS idx_user_packages_created ON user_packages(created_at)",
            
            # User free posts table indexes
            "CREATE INDEX IF NOT EXISTS idx_user_free_posts_user_id ON user_free_posts(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_free_posts_next_free ON user_free_posts(next_free_post_at)",
            
            # Post boost schedule table indexes
            "CREATE INDEX IF NOT EXISTS idx_post_boost_schedule_post_id ON post_boost_schedule(post_id)",
            "CREATE INDEX IF NOT EXISTS idx_post_boost_schedule_next_boost ON post_boost_schedule(next_boost_at)",
            "CREATE INDEX IF NOT EXISTS idx_post_boost_schedule_active ON post_boost_schedule(is_active)",
            
            # AI moderation log indexes
            "CREATE INDEX IF NOT EXISTS idx_ai_moderation_log_post_id ON ai_moderation_log(post_id)",
            "CREATE INDEX IF NOT EXISTS idx_ai_moderation_log_moderated_at ON ai_moderation_log(moderated_at)",
        ]
        
        for index_sql in indexes:
            try:
                await db.execute(index_sql)
            except Exception as e:
                print(f"Warning: Could not create index: {e}")
    
    
    async def init_default_data(self, db):
        """Initialize default categories, currencies, and cities"""
        # Check if data already exists
        cursor = await db.execute("SELECT COUNT(*) FROM super_rubrics")
        count = await cursor.fetchone()
        if count[0] > 0:
            return
        
        # Insert default currencies
        currencies = [
            ("rub-id", "RUB", "Российский рубль", "Російський рубль", "₽", 1, datetime.now().isoformat()),
            ("usd-id", "USD", "Доллар США", "Долар США", "$", 1, datetime.now().isoformat()),
            ("eur-id", "EUR", "Евро", "Євро", "€", 1, datetime.now().isoformat()),
            ("uah-id", "UAH", "Украинская гривна", "Українська гривня", "₴", 1, datetime.now().isoformat()),
        ]
        
        for currency in currencies:
            await db.execute(
                "INSERT INTO currencies (id, code, name_ru, name_ua, symbol, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                currency
            )
        
        # Insert default super rubrics
        super_rubrics = [
            ("job-rubric", "Работа", "Робота", "💼", 1),
            ("service-rubric", "Услуги", "Послуги", "🛠️", 1),
        ]
        
        for rubric in super_rubrics:
            await db.execute(
                "INSERT INTO super_rubrics (id, name_ru, name_ua, icon, is_active) VALUES (?, ?, ?, ?, ?)",
                rubric
            )
        
        # Insert default cities
        cities = [
            ("moscow-city", "Москва", "Москва", 1),
            ("spb-city", "Санкт-Петербург", "Санкт-Петербург", 1),
            ("kiev-city", "Киев", "Київ", 1),
            ("kharkiv-city", "Харьков", "Харків", 1),
            ("odessa-city", "Одесса", "Одеса", 1),
            ("minsk-city", "Минск", "Мінск", 1),
        ]
        
        for city in cities:
            await db.execute(
                "INSERT INTO cities (id, name_ru, name_ua, is_active) VALUES (?, ?, ?, ?)",
                city
            )
        
        # Insert default app settings
        await db.execute(
            "INSERT INTO app_settings (id, updated_at) VALUES (?, ?)",
            ("default", datetime.now().isoformat())
        )
        
        # Insert default packages
        packages = [
            (
                "free-package", "Бесплатный", "Безкоштовний", "free", 0, "rub-id", 7, 30,
                "1 объявление в неделю|Базовое размещение", "1 оголошення на тиждень|Базове розміщення",
                0, 0, 0, None, 1, 1, datetime.now().isoformat(), datetime.now().isoformat()
            ),
            (
                "standard-package", "Стандарт", "Стандарт", "standard", 100, "rub-id", 30, 30,
                "Стандартное размещение|30 дней активности", "Стандартне розміщення|30 днів активності", 
                0, 0, 0, None, 1, 2, datetime.now().isoformat(), datetime.now().isoformat()
            ),
            (
                "photo-package", "С фото", "З фото", "photo", 150, "rub-id", 30, 30,
                "Возможность добавить фото|30 дней активности", "Можливість додати фото|30 днів активності",
                1, 0, 0, None, 1, 3, datetime.now().isoformat(), datetime.now().isoformat()
            ),
            (
                "highlight-package", "Выделение", "Виділення", "highlight", 200, "rub-id", 14, 30,
                "Выделение цветом|14 дней выделения", "Виділення кольором|14 днів виділення",
                0, 1, 0, None, 1, 4, datetime.now().isoformat(), datetime.now().isoformat()
            ),
            (
                "boost-package", "Больше показов", "Більше показів", "boost", 300, "rub-id", 7, 30,
                "Поднятие каждые 3 дня|7 дней активности", "Підняття кожні 3 дні|7 днів активності",
                0, 0, 1, 3, 1, 5, datetime.now().isoformat(), datetime.now().isoformat()
            )
        ]
        
        for package in packages:
            await db.execute(
                """INSERT INTO packages (id, name_ru, name_ua, package_type, price, currency_id, 
                   duration_days, post_lifetime_days, features_ru, features_ua, has_photo, 
                   has_highlight, has_boost, boost_interval_days, is_active, sort_order, 
                   created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                package
            )
        
        await db.commit()
        print("Default data initialized successfully")

    async def execute(self, query, params=None):
        """Execute a query and return results"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params or ())
            await db.commit()
            return cursor
    
    async def fetchall(self, query, params=None):
        """Fetch all results from a query"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params or ())
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def fetchone(self, query, params=None):
        """Fetch one result from a query"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params or ())
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def insert(self, table, data):
        """Insert data into a table"""
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, list(data.values()))
            await db.commit()
            return data['id']
    
    async def update(self, table, data, where_clause, where_params):
        """Update data in a table"""
        data['updated_at'] = datetime.now().isoformat()
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, list(data.values()) + list(where_params))
            await db.commit()
            return cursor.rowcount
    
    async def delete(self, table, where_clause, where_params):
        """Delete data from a table"""
        query = f"DELETE FROM {table} WHERE {where_clause}"
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, where_params)
            await db.commit()
            return cursor.rowcount

# Global database instance
db = Database()