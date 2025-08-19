from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URL: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

client: AsyncIOMotorClient | None = None
db = None

async def connect_to_mongo():
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URL)

    db_name = client.get_default_database().name if client.get_default_database() else "smart_learning_db"
    db = client[db_name]

    print(f"✅ Connected to MongoDB database: {db_name}")

async def close_mongo_connection():
    global client
    if client:
        client.close()
        print("❌ MongoDB connection closed")
