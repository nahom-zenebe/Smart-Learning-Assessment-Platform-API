"""Unit tests for QuestionService (validation + quiz linking rules)."""

import pytest
from fastapi import HTTPException

from models.Question import QuestionCreate, QuestionUpdate
from models.Quiz import QuizCreate
from services.question_service import QuestionService
from services.quiz_service import QuizService

VALID_ID = "64b1f0c0a1b2c3d4e5f60718"


@pytest.fixture
def question_service(fake_db) -> QuestionService:
    return QuestionService()


@pytest.fixture
def quiz_service(fake_db) -> QuizService:
    return QuizService()


async def create_quiz(quiz_service: QuizService, title="Sample Quiz Title") -> dict:
    return await quiz_service.create_quiz(
        QuizCreate(lesson_id="lesson-1", title=title)
    )


def make_question_data(quiz_id: str, **overrides) -> QuestionCreate:
    data = {
        "quiz_id": quiz_id,
        "text": "What is 2 + 2?",
        "options": ["3", "4", "5"],
        "correct_option_id": "1",
    }
    data.update(overrides)
    return QuestionCreate(**data)


class TestCorrectOptionValidation:
    @pytest.mark.asyncio
    async def test_valid_index_passes(self, question_service):
        question_service._validate_correct_option(["a", "b", "c"], "2")  # no raise

    @pytest.mark.asyncio
    async def test_empty_options_rejected(self, question_service):
        with pytest.raises(HTTPException) as exc:
            question_service._validate_correct_option([], "0")
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_non_numeric_index_rejected(self, question_service):
        with pytest.raises(HTTPException) as exc:
            question_service._validate_correct_option(["a"], "abc")
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_negative_index_rejected(self, question_service):
        with pytest.raises(HTTPException) as exc:
            question_service._validate_correct_option(["a"], "-1")
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_out_of_range_index_rejected(self, question_service):
        with pytest.raises(HTTPException) as exc:
            question_service._validate_correct_option(["a", "b"], "2")
        assert exc.value.status_code == 400
        assert "between 0 and 1" in exc.value.detail


class TestCreateQuestion:
    @pytest.mark.asyncio
    async def test_creates_and_links_to_quiz(self, question_service, quiz_service):
        quiz = await create_quiz(quiz_service)

        question = await question_service.create_question(
            make_question_data(quiz["id"])
        )

        assert question["id"]
        assert question["quiz_id"] == quiz["id"]
        assert question["correct_option_id"] == "1"

        refreshed_quiz = await quiz_service.get_quiz(quiz["id"])
        assert refreshed_quiz["questions"] == [question["id"]]

    @pytest.mark.asyncio
    async def test_unknown_quiz_rejected(self, question_service):
        with pytest.raises(HTTPException) as exc:
            await question_service.create_question(make_question_data(VALID_ID))
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_correct_option_not_linked(
        self, question_service, quiz_service
    ):
        quiz = await create_quiz(quiz_service)

        with pytest.raises(HTTPException) as exc:
            await question_service.create_question(
                make_question_data(quiz["id"], correct_option_id="9")
            )
        assert exc.value.status_code == 400

        refreshed_quiz = await quiz_service.get_quiz(quiz["id"])
        assert refreshed_quiz["questions"] == []  # nothing was linked
