from typing import List

from fastapi import APIRouter, status

from models.Course import Course, CourseCreate, CourseUpdate
from services.course_service import CourseService

router = APIRouter(prefix="/courses", tags=["Courses"])
service = CourseService()


@router.post(
    "/", response_model=Course, status_code=status.HTTP_201_CREATED
)
async def create_course(course: CourseCreate):
    return await service.create_course(course)


@router.get("/", response_model=List[Course], status_code=status.HTTP_200_OK)
async def list_courses(limit: int = 100):
    return await service.list_courses(limit)


@router.get(
    "/{course_id}", response_model=Course, status_code=status.HTTP_200_OK
)
async def get_course(course_id: str):
    return await service.get_course(course_id)


@router.put(
    "/{course_id}", response_model=Course, status_code=status.HTTP_200_OK
)
async def update_course(course_id: str, course: CourseUpdate):
    return await service.update_course(course_id, course)


@router.delete("/{course_id}", status_code=status.HTTP_200_OK)
async def delete_course(course_id: str):
    await service.delete_course(course_id)
    return {"message": "Course deleted successfully", "id": course_id}
