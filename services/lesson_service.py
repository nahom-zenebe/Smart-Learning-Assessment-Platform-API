from repositories.lesson_repository import LessonRepository
from models.lesson import Lesson

class LessonService:
    def __init__(self):
        self.repo = LessonRepository()

    async def create_lesson(self, lesson: Lesson):
        lesson_data = lesson.dict(by_alias=True)
        lesson_id = await self.repo.create(lesson_data)
        return await self.repo.get_by_id(lesson_id)

    async def get_lesson(self, lesson_id: str):
        return await self.repo.get_by_id(lesson_id)

    async def list_lessons(self):
        return await self.repo.list_all()

    async def update_lesson(self, lesson_id: str, data: dict):
        return await self.repo.update(lesson_id, data)

    async def delete_lesson(self, lesson_id: str):
        return await self.repo.delete(lesson_id)
