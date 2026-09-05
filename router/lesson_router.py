
from typing import List

from fastapi import APIRouter, status

from models.Lesson import Lesson, LessonCreate, LessonUpdate
from services.lesson_service import LessonService

router = APIRouter(prefix="/lessons", tags=["Lessons"])
service = LessonService()


@router.post(
    "/", response_model=Lesson, status_code=status.HTTP_201_CREATED
)
async def create_lesson(lesson: LessonCreate):
    return await service.create_lesson(lesson)


@router.get("/", response_model=List[Lesson], status_code=status.HTTP_200_OK)
async def list_lessons(limit: int = 100):
    return await service.list_lessons(limit)


@router.get(
    "/{lesson_id}", response_model=Lesson, status_code=status.HTTP_200_OK
)
async def get_lesson(lesson_id: str):
    return await service.get_lesson(lesson_id)


@router.put(
    "/{lesson_id}", response_model=Lesson, status_code=status.HTTP_200_OK
)
async def update_lesson(lesson_id: str, lesson: LessonUpdate):
    return await service.update_lesson(lesson_id, lesson)


@router.delete("/{lesson_id}", status_code=status.HTTP_200_OK)
async def delete_lesson(lesson_id: str):
    await service.delete_lesson(lesson_id)
    return {"message": "Lesson deleted successfully", "id": lesson_id}

