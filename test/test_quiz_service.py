"""Unit tests for QuizService."""

import pytest
from fastapi import HTTPException

from models.Quiz import QuizCreate, QuizUpdate
from services.quiz_service import QuizService

VALID_ID = "64b1f0c0a1b2c3d4e5f60718"


@pytest.fixture
def service(fake_db) -> QuizService:
    return QuizService()


def make_quiz_data(**overrides) -> QuizCreate:
    data = {
        "lesson_id": "lesson-1",
        "title": "Chapter 1 Quiz",
        "description": "Covers chapter 1",
        "questions": [],
    }
    data.update(overrides)
    return QuizCreate(**data)


@pytest.mark.asyncio
async def test_create_quiz_persists_and_returns(service):
    quiz = await service.create_quiz(make_quiz_data())

    assert quiz["title"] == "Chapter 1 Quiz"
    assert quiz["lesson_id"] == "lesson-1"
    assert quiz["questions"] == []
    assert quiz["id"]


@pytest.mark.asyncio
async def test_get_quiz(service):
    created = await service.create_quiz(make_quiz_data())
    fetched = await service.get_quiz(created["id"])
    assert fetched["id"] == created["id"]
    assert fetched["description"] == "Covers chapter 1"


@pytest.mark.asyncio
async def test_get_quiz_not_found(service):
    with pytest.raises(HTTPException) as exc:
        await service.get_quiz(VALID_ID)
    assert exc.value.status_code == 404
    assert VALID_ID in exc.value.detail


@pytest.mark.asyncio
async def test_get_quiz_invalid_id_returns_404(service):
    with pytest.raises(HTTPException) as exc:
        await service.get_quiz("not-a-real-id")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_list_quizzes(service):
    await service.create_quiz(make_quiz_data(title="Quiz One Title"))
    await service.create_quiz(make_quiz_data(title="Quiz Two Title"))

    quizzes = await service.list_quizzes()

    assert len(quizzes) == 2
    assert {q["title"] for q in quizzes} == {"Quiz One Title", "Quiz Two Title"}


@pytest.mark.asyncio
async def test_list_quizzes_respects_limit(service):
    for index in range(4):
        await service.create_quiz(make_quiz_data(title=f"Quiz Number {index}"))

    assert len(await service.list_quizzes(limit=2)) == 2


@pytest.mark.asyncio
async def test_update_quiz_partial_fields_only(service):
    created = await service.create_quiz(make_quiz_data())

    updated = await service.update_quiz(
        created["id"], QuizUpdate(title="Renamed Quiz Title")
    )

    assert updated["title"] == "Renamed Quiz Title"
    assert updated["lesson_id"] == "lesson-1"  # untouched field stays
    assert updated["questions"] == []


@pytest.mark.asyncio
async def test_update_quiz_not_found(service):
    with pytest.raises(HTTPException) as exc:
        await service.update_quiz(VALID_ID, QuizUpdate(title="Ghost Quiz Title"))
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_quiz(service):
    created = await service.create_quiz(make_quiz_data())

    await service.delete_quiz(created["id"])

    with pytest.raises(HTTPException):
        await service.get_quiz(created["id"])


@pytest.mark.asyncio
async def test_delete_quiz_not_found(service):
    with pytest.raises(HTTPException) as exc:
        await service.delete_quiz(VALID_ID)
    assert exc.value.status_code == 404
