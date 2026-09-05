from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGODB_URL: str = "mongodb://localhost:27017"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()

client: Optional[AsyncIOMotorClient] = None
db = None


async def connect_to_mongo() -> None:
    global client, db
    mongodb_url = settings.MONGODB_URL or "mongodb://localhost:27017"
    client = AsyncIOMotorClient(mongodb_url)

    default_db = client.get_default_database()
    db_name = default_db.name if default_db else "smart_learning_db"
    db = client[db_name]

    print(f"✅ Connected to MongoDB database: {db_name}")


async def close_mongo_connection() -> None:
    global client
    if client:
        client.close()
        print("❌ MongoDB connection closed")


def get_database():
    """Return the shared database handle (set during app startup).

    Repositories must resolve the database at call time through this helper
    instead of importing ``db`` directly, because the module-level ``db``
    variable only exists after ``connect_to_mongo()`` runs.
    """
    if db is None:
        raise RuntimeError(
            "MongoDB is not connected yet - the application startup event did not run."
        )
    return db


def serialize_doc(doc: Any) -> Optional[dict]:
    """Convert a raw Mongo document into a JSON-friendly dict.

    Renames ``_id`` to ``id`` (as a string) so responses never leak BSON ids.
    """
    if doc is None:
        return None
    doc = dict(doc)
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)
    return doc

