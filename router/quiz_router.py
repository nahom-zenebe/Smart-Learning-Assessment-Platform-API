from typing import List

from fastapi import APIRouter, status

from models.Question import Question
from models.Quiz import Quiz, QuizCreate, QuizUpdate
from services.question_service import QuestionService
from services.quiz_service import QuizService

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])
service = QuizService()
question_service = QuestionService()


@router.post("/", response_model=Quiz, status_code=status.HTTP_201_CREATED)
async def create_quiz(quiz: QuizCreate):
    return await service.create_quiz(quiz)


@router.get("/", response_model=List[Quiz], status_code=status.HTTP_200_OK)
async def list_quizzes(limit: int = 100):
    return await service.list_quizzes(limit)


@router.get("/{quiz_id}", response_model=Quiz, status_code=status.HTTP_200_OK)
async def get_quiz(quiz_id: str):
    return await service.get_quiz(quiz_id)


@router.get(
    "/{quiz_id}/questions",
    response_model=List[Question],
    status_code=status.HTTP_200_OK,
)
async def get_quiz_questions(quiz_id: str):
    """All questions of a quiz, ordered for taking the quiz."""
    return await question_service.list_questions_by_quiz(quiz_id)


@router.put("/{quiz_id}", response_model=Quiz, status_code=status.HTTP_200_OK)
async def update_quiz(quiz_id: str, quiz: QuizUpdate):
    return await service.update_quiz(quiz_id, quiz)


@router.delete("/{quiz_id}", status_code=status.HTTP_200_OK)
async def delete_quiz(quiz_id: str):
    await service.delete_quiz(quiz_id)
    return {"message": "Quiz deleted successfully", "id": quiz_id}
