from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

class Database:
    client: AsyncIOMotorClient = None
    database = None

database = Database()

async def get_database():
    return database.database

async def connect_to_mongo():
    database.client = AsyncIOMotorClient(settings.mongo_url)
    database.database = database.client[settings.db_name]
    print(f"Connected to MongoDB: {settings.db_name}")

async def close_mongo_connection():
    if database.client:
        database.client.close()
        print("Disconnected from MongoDB")