from typing import Optional

from db.mongodb import get_database, serialize_doc


class UserRepository:
    COLLECTION = "users"

    @property
    def collection(self):
        return get_database()[self.COLLECTION]

    async def create_user(self, user) -> object:
        """Insert a UserInDB model and return it with the generated id set."""
        data = user.model_dump(exclude={"id"})
        result = await self.collection.insert_one(data)
        user.id = str(result.inserted_id)
        return user

    async def get_by_email(self, email: str):
        from models.User import UserInDB

        doc = await self.collection.find_one({"email": email})
        if not doc:
            return None
        doc = serialize_doc(doc)
        return UserInDB(**doc)
