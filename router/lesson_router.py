
from fastapi import APIRouter, HTTPException
from services.lesson_service import LessonService
from models.lesson import Lesson



router=APIRouter(prefix="/lessons", tags=["Lessons"])
service=LessonService()



@router.post('/',response_mode=Lesson)
async def create_lesson(lesson:Lesson):
    return await service.create_lesson(lesson)

router.get("/{lesson_id}", response_model=Lesson)
async def get_lesson(lesson_id: str):
    lesson = await service.get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson

@router.get("/", response_model=list[Lesson])
async def list_lessons():
    return await service.list_lessons()

@router.put("/{lesson_id}", response_model=Lesson)
async def update_lesson(lesson_id: str, lesson: Lesson):
    updated = await service.update_lesson(lesson_id, lesson.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return updated

@router.delete("/{lesson_id}")
async def delete_lesson(lesson_id: str):
    deleted = await service.delete_lesson(lesson_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"message": "Lesson deleted successfully"}

