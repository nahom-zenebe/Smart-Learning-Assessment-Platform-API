from typing import List, Optional

from bson import ObjectId

from db.mongodb import get_database, serialize_doc


class ProgressRepository:
    COLLECTION = "progress"

    @property
    def collection(self):
        return get_database()[self.COLLECTION]

    async def create(self, data: dict) -> str:
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def get_by_id(self, progress_id: str) -> Optional[dict]:
        if not ObjectId.is_valid(progress_id):
            return None
        doc = await self.collection.find_one({"_id": ObjectId(progress_id)})
        return serialize_doc(doc)

    async def find_by_user_and_course(
        self, user_id: str, course_id: str
    ) -> Optional[dict]:
        """One progress document per (user, course) pair."""
        doc = await self.collection.find_one(
            {"user_id": user_id, "course_id": course_id}
        )
        return serialize_doc(doc)

    async def list_all(
        self,
        user_id: Optional[str] = None,
        course_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[dict]:
        query: dict = {}
        if user_id:
            query["user_id"] = user_id
        if course_id:
            query["course_id"] = course_id
        cursor = self.collection.find(query).sort("_id", -1).limit(limit)
        return [serialize_doc(doc) for doc in await cursor.to_list(length=limit)]

    async def update(self, progress_id: str, data: dict) -> Optional[dict]:
        if not ObjectId.is_valid(progress_id):
            return None
        await self.collection.update_one(
            {"_id": ObjectId(progress_id)}, {"$set": data}
        )
        return await self.get_by_id(progress_id)

    async def delete(self, progress_id: str) -> bool:
        if not ObjectId.is_valid(progress_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(progress_id)})
        return result.deleted_count > 0
