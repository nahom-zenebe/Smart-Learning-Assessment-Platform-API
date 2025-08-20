from repositories.course_repository import CourseRepository
from models.Course import Course



class CourseService:
    def __init__(self):
        self.course=CourseRepository()

    async def create_course(self,course:Course):
        course_data = course.dict(by_alias=True)
        course_id=await self.course.createCourse(course_data)
        return await self.course.get_by_id(course_id)

    async def get_course(self):
        return await self.course.get_allcourse()


    async def update_course(self,course:Course,course_id:str):
        return await self.course.updatecourse(course,course_id)

    
    async def delete_course(self,course_id:str):
        return await self.course.delete(course_id)
