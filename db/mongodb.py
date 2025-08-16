from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str
    MONGO_DB_NAME: str

    class Config:
        env_file = ".env"  

settings = Settings()

client: AsyncIOMotorClient | None = None
db = None

async def connect_to_mongo():
    global client, db
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB_NAME]
    print(f"✅ Connected to MongoDB database: {settings.MONGO_DB_NAME}")

async def close_mongo_connection():
    global client
    if client:
        client.close()
        print("❌ MongoDB connection closed")
