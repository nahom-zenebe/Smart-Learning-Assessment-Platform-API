from typing import List

from fastapi import HTTPException, status

from models.Course import CourseCreate, CourseUpdate
from repositories.course_repository import CourseRepository


class CourseService:
    def __init__(self):
        self.repo = CourseRepository()

    async def create_course(self, data: CourseCreate) -> dict:
        course_id = await self.repo.create(data.model_dump())
        return await self.repo.get_by_id(course_id)

    async def get_course(self, course_id: str) -> dict:
        course = await self.repo.get_by_id(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course {course_id} not found",
            )
        return course

    async def list_courses(self, limit: int = 100) -> List[dict]:
        return await self.repo.list_all(limit)

    async def update_course(self, course_id: str, data: CourseUpdate) -> dict:
        await self.get_course(course_id)
        updated = await self.repo.update(
            course_id, data.model_dump(exclude_unset=True)
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course {course_id} not found",
            )
        return updated

    async def delete_course(self, course_id: str) -> None:
        if not await self.repo.delete(course_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course {course_id} not found",
            )
