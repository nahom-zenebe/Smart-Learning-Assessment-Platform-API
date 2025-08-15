# app/db/mongo.py
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "learning_platform"

    class Config:
        env_file = ".env"

settings = Settings()

client: AsyncIOMotorClient = None
db = None

async def connect_to_mongo():
    global client, db
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB_NAME]
    print("✅ Connected to MongoDB")


async def close_mongo_connection():
    global client
    client.close()
    print("❌ MongoDB connection closed")
