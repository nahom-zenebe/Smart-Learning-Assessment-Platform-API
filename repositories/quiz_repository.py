from typing import List, Optional

from bson import ObjectId

from db.mongodb import get_database, serialize_doc


class QuizRepository:
    COLLECTION = "quizzes"

    @property
    def collection(self):
        return get_database()[self.COLLECTION]

    async def create(self, data: dict) -> str:
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def get_by_id(self, quiz_id: str) -> Optional[dict]:
        if not ObjectId.is_valid(quiz_id):
            return None
        doc = await self.collection.find_one({"_id": ObjectId(quiz_id)})
        return serialize_doc(doc)

    async def list_all(self, limit: int = 100) -> List[dict]:
        cursor = self.collection.find().sort("_id", -1).limit(limit)
        return [serialize_doc(doc) for doc in await cursor.to_list(length=limit)]

    async def update(self, quiz_id: str, data: dict) -> Optional[dict]:
        if not ObjectId.is_valid(quiz_id):
            return None
        await self.collection.update_one(
            {"_id": ObjectId(quiz_id)}, {"$set": data}
        )
        return await self.get_by_id(quiz_id)

    async def delete(self, quiz_id: str) -> bool:
        if not ObjectId.is_valid(quiz_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(quiz_id)})
        return result.deleted_count > 0

    async def push_question(self, quiz_id: str, question_id: str) -> None:
        """Link a question to its quiz (no duplicates)."""
        if not ObjectId.is_valid(quiz_id):
            return
        await self.collection.update_one(
            {"_id": ObjectId(quiz_id)},
            {"$addToSet": {"questions": question_id}},
        )

    async def pull_question(self, quiz_id: str, question_id: str) -> None:
        """Unlink a question from its quiz."""
        if not ObjectId.is_valid(quiz_id):
            return
        await self.collection.update_one(
            {"_id": ObjectId(quiz_id)},
            {"$pull": {"questions": question_id}},
        )
