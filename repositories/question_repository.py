from db.mongo import db
from bson import ObjectId


class QuestionRepository:
    def __init__(self):
        self.collection=db.get_collection("Question")

    async def create(self,Question:dict):
        result=await self.collection.insert_one(Question)
        return result
    async def getallquestion(self):
        result=await self.collection.find({})

    async def update(self,updatedQuetion:dict,Question_id:str):
        result=await self.collection.update_one(
            {"_id",ObjectId(Question_id)},
            {"$set",updatedQuetion}
        )

    async def getsingleQuestion(self,Question_id:str):
        result=await self.collection.find_one({"id":ObjectId(Question_id)})
        

    async def deleteQuestion(self,Question_id:str):
        result=await self.collection.delete_one({"_id":Object(Question_id)})


    