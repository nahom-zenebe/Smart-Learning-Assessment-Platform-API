from typing import List, Optional

from bson import ObjectId

from db.mongodb import get_database, serialize_doc


class SubmissionRepository:
    COLLECTION = "submissions"

    @property
    def collection(self):
        return get_database()[self.COLLECTION]

    async def create(self, data: dict) -> str:
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def get_by_id(self, submission_id: str) -> Optional[dict]:
        if not ObjectId.is_valid(submission_id):
            return None
        doc = await self.collection.find_one({"_id": ObjectId(submission_id)})
        return serialize_doc(doc)

    async def list_all(
        self,
        user_id: Optional[str] = None,
        quiz_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[dict]:
        query: dict = {}
        if user_id:
            query["user_id"] = user_id
        if quiz_id:
            query["quiz_id"] = quiz_id
        cursor = self.collection.find(query).sort("_id", -1).limit(limit)
        return [serialize_doc(doc) for doc in await cursor.to_list(length=limit)]

    async def delete(self, submission_id: str) -> bool:
        if not ObjectId.is_valid(submission_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(submission_id)})
        return result.deleted_count > 0
