from typing import List

from fastapi import APIRouter, HTTPException, status

from models.Question import Question, QuestionCreate, QuestionUpdate
from services.question_service import QuestionService

router = APIRouter(prefix="/questions", tags=["Questions"])
service = QuestionService()


@router.post(
    "/", response_model=Question, status_code=status.HTTP_201_CREATED
)
async def create_question(question: QuestionCreate):
    """Create a question and link it to its quiz.

    ``correct_option_id`` must be the index (as a string) of the correct
    option inside ``options``, e.g. options=["A", "B", "C"] -> "1" means B.
    """
    return await service.create_question(question)


@router.get(
    "/", response_model=List[Question], status_code=status.HTTP_200_OK
)
async def list_questions(limit: int = 100):
    return await service.list_questions(limit)


@router.get(
    "/{question_id}", response_model=Question, status_code=status.HTTP_200_OK
)
async def get_question(question_id: str):
    return await service.get_question(question_id)


@router.put(
    "/{question_id}", response_model=Question, status_code=status.HTTP_200_OK
)
async def update_question(question_id: str, question: QuestionUpdate):
    return await service.update_question(question_id, question)


@router.delete("/{question_id}", status_code=status.HTTP_200_OK)
async def delete_question(question_id: str):
    await service.delete_question(question_id)
    return {"message": "Question deleted successfully", "id": question_id}

