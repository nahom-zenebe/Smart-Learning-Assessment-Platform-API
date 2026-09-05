from typing import List, Optional

from bson import ObjectId

from db.mongodb import get_database, serialize_doc


class NotificationRepository:
    COLLECTION = "notifications"

    @property
    def collection(self):
        return get_database()[self.COLLECTION]

    async def create(self, data: dict) -> str:
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def get_by_id(self, notification_id: str) -> Optional[dict]:
        if not ObjectId.is_valid(notification_id):
            return None
        doc = await self.collection.find_one({"_id": ObjectId(notification_id)})
        return serialize_doc(doc)

    async def list_for_user(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[dict]:
        query: dict = {"user_id": user_id}
        if unread_only:
            query["read"] = False
        cursor = self.collection.find(query).sort("_id", -1).limit(limit)
        return [serialize_doc(doc) for doc in await cursor.to_list(length=limit)]

    async def unread_count(self, user_id: str) -> int:
        return await self.collection.count_documents(
            {"user_id": user_id, "read": False}
        )

    async def mark_read(self, notification_id: str) -> Optional[dict]:
        if not ObjectId.is_valid(notification_id):
            return None
        await self.collection.update_one(
            {"_id": ObjectId(notification_id)}, {"$set": {"read": True}}
        )
        return await self.get_by_id(notification_id)

    async def mark_all_read(self, user_id: str) -> int:
        result = await self.collection.update_many(
            {"user_id": user_id, "read": False}, {"$set": {"read": True}}
        )
        return result.modified_count

    async def delete(self, notification_id: str) -> bool:
        if not ObjectId.is_valid(notification_id):
            return False
        result = await self.collection.delete_one(
            {"_id": ObjectId(notification_id)}
        )
        return result.deleted_count > 0