from typing import List

from fastapi import HTTPException, status

from models.Lesson import LessonCreate, LessonUpdate
from repositories.lesson_repository import LessonRepository


class LessonService:
    def __init__(self):
        self.repo = LessonRepository()

    async def create_lesson(self, data: LessonCreate) -> dict:
        lesson_id = await self.repo.create(data.model_dump())
        return await self.repo.get_by_id(lesson_id)

    async def get_lesson(self, lesson_id: str) -> dict:
        lesson = await self.repo.get_by_id(lesson_id)
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson {lesson_id} not found",
            )
        return lesson

    async def list_lessons(self, limit: int = 100) -> List[dict]:
        return await self.repo.list_all(limit)

    async def update_lesson(self, lesson_id: str, data: LessonUpdate) -> dict:
        await self.get_lesson(lesson_id)
        updated = await self.repo.update(
            lesson_id, data.model_dump(exclude_unset=True)
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson {lesson_id} not found",
            )
        return updated

    async def delete_lesson(self, lesson_id: str) -> None:
        if not await self.repo.delete(lesson_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson {lesson_id} not found",
            )
