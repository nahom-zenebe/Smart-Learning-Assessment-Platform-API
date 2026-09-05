from typing import List, Optional

from bson import ObjectId

from db.mongodb import get_database, serialize_doc


class QuestionRepository:
    COLLECTION = "questions"

    @property
    def collection(self):
        return get_database()[self.COLLECTION]

    async def create(self, data: dict) -> str:
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def get_by_id(self, question_id: str) -> Optional[dict]:
        if not ObjectId.is_valid(question_id):
            return None
        doc = await self.collection.find_one({"_id": ObjectId(question_id)})
        return serialize_doc(doc)

    async def list_all(self, limit: int = 100) -> List[dict]:
        cursor = self.collection.find().sort("_id", -1).limit(limit)
        return [serialize_doc(doc) for doc in await cursor.to_list(length=limit)]

    async def get_by_quiz(self, quiz_id: str, limit: int = 500) -> List[dict]:
        """All questions of a quiz, in creation order (stable for scoring)."""
        cursor = (
            self.collection.find({"quiz_id": quiz_id})
            .sort("_id", 1)
            .limit(limit)
        )
        return [serialize_doc(doc) for doc in await cursor.to_list(length=limit)]

    async def update(self, question_id: str, data: dict) -> Optional[dict]:
        if not ObjectId.is_valid(question_id):
            return None
        await self.collection.update_one(
            {"_id": ObjectId(question_id)}, {"$set": data}
        )
        return await self.get_by_id(question_id)

    async def delete(self, question_id: str) -> bool:
        if not ObjectId.is_valid(question_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(question_id)})
        return result.deleted_count > 0
