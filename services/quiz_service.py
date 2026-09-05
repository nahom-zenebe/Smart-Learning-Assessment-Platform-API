from typing import List

from fastapi import HTTPException, status

from models.Quiz import QuizCreate, QuizUpdate
from repositories.quiz_repository import QuizRepository


class QuizService:
    def __init__(self):
        self.repo = QuizRepository()

    async def create_quiz(self, data: QuizCreate) -> dict:
        quiz_id = await self.repo.create(data.model_dump())
        return await self.repo.get_by_id(quiz_id)

    async def get_quiz(self, quiz_id: str) -> dict:
        quiz = await self.repo.get_by_id(quiz_id)
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz {quiz_id} not found",
            )
        return quiz

    async def list_quizzes(self, limit: int = 100) -> List[dict]:
        return await self.repo.list_all(limit)

    async def update_quiz(self, quiz_id: str, data: QuizUpdate) -> dict:
        await self.get_quiz(quiz_id)
        updated = await self.repo.update(
            quiz_id, data.model_dump(exclude_unset=True)
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz {quiz_id} not found",
            )
        return updated

    async def delete_quiz(self, quiz_id: str) -> None:
        if not await self.repo.delete(quiz_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz {quiz_id} not found",
            )
