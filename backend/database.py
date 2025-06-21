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
        """Initialize database with all required tables"""
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
                    status INTEGER DEFAULT 3,
                    views_count INTEGER DEFAULT 0,
                    is_premium BOOLEAN DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (currency_id) REFERENCES currencies (id),
                    FOREIGN KEY (city_id) REFERENCES cities (id),
                    FOREIGN KEY (super_rubric_id) REFERENCES super_rubrics (id),
                    FOREIGN KEY (author_id) REFERENCES users (id)
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
                    mistral_api_key TEXT,
                    app_name TEXT DEFAULT 'Telegram Marketplace',
                    app_description TEXT DEFAULT 'Платформа частных объявлений',
                    free_posts_per_week INTEGER DEFAULT 1,
                    moderation_enabled BOOLEAN DEFAULT 1,
                    updated_at TEXT
                )
            """)
            
            await db.commit()
            
            # Initialize default data
            await self.init_default_data(db)
    
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