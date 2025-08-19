
from db.mongo import db
from bson import ObjectId

class CourseRepository:
    def __init__(self):
        self.collection=db.get_collection("Course")

    async def createCourse(self,course:dict):
        result=await self.collection.insert_one(couurse)
        return str(result._id)

    async def get_by_id(self,course_id):
        result=await self.collection.find_one({"id":ObjectId(course_id)})
        return result


    async def get_allcourse(self):
        result=await self.collection.find({})
        return [doc async for doc in result]


    async def updatecourse(self,updatedcourse,course_id):
        result=await self.collection.update_one(
            {"id":Object(course_id)},
            {"$set":updated_data}
        )
        return await  result
    
    async def delete(self,course_id:str):
        result=await self.collection.delete_one({"id":Object(course_id)})



    
