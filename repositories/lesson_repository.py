from db.mongo import db
from bson import ObjectId


class LessonRepository:
    def __init__(self):
        self.collection=db.get_collection('lessons')

    async def create(self,lesson_data:dict):
        result=await self.collection.insert_one(lesson_data)
        return str(result.inserted_id)

    async def get_by_id(self,lesson_id:str):
        result=await self.collection.find_one({"id":ObjectId(lesson_id)})
        return result

    async def list_all(self):
        result=await self.collection.find({})
        return [doc async for doc in result]


    async def update(self,lesson_id:str,update_data:dict):
        result=await self.collection.update_one(
            {"_id",ObjectId(lesson_id)},
            {"$set",update_data},
        )

         return await self.get_by_id(lesson_id)

    async def delete(self,lesson_id:str):
        result=await self.collection.delete_one({"_id":Object(lesson_id)})

     