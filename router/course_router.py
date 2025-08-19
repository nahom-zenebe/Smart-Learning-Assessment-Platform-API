from fastapi import APIRouter, HTTPException
from service.course_service import CourseService
from models.Course import Course



router=APIRouter(prefix="/course",tag=['course'])
service=CourseService()


@router.post('/',response_model=Course,status_code=status.HTTP_201_CREATED)
async def create_course(course:Coure):
    return await service.create_course(course)

@router.get('/',response_model=[Course],status_code=status.HTTP_200_OK)
async def getallcourse():
    return await service.get_course()

@router.put('/',reponse_model=Course)
async def updatecourse(course:Course,course_id:str):
    return await service.update_course(course,course_id)

@router.delete('/',response_model=Course)
async def deletecourse(course_id:str):
     deleted = await service.delete_course(course_id)
     if not deleted:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"message": "Course deleted successfully"}