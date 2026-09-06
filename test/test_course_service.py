"""Unit tests for CourseService."""

import pytest
from fastapi import HTTPException

from models.Course import CourseCreate, CourseUpdate
from services.course_service import CourseService

VALID_ID = "64b1f0c0a1b2c3d4e5f60718"


@pytest.fixture
def service(fake_db) -> CourseService:
    return CourseService()


def make_course_data(**overrides) -> CourseCreate:
    data = {
        "title": "Python 101 Basics",
        "description": "Intro to Python",
        "instructor_id": "instructor-1",
        "category": "programming",
        "tags": ["python", "beginner"],
        "lessons": ["lesson-1"],
    }
    data.update(overrides)
    return CourseCreate(**data)


@pytest.mark.asyncio
async def test_create_course_persists_and_returns(service):
    course = await service.create_course(make_course_data())

    assert course["title"] == "Python 101 Basics"
    assert course["instructor_id"] == "instructor-1"
    assert course["tags"] == ["python", "beginner"]
    assert course["id"]
    assert course["created_at"]


@pytest.mark.asyncio
async def test_get_course(service):
    created = await service.create_course(make_course_data())
    fetched = await service.get_course(created["id"])
    assert fetched["id"] == created["id"]
    assert fetched["description"] == "Intro to Python"


@pytest.mark.asyncio
async def test_get_course_not_found(service):
    with pytest.raises(HTTPException) as exc:
        await service.get_course(VALID_ID)
    assert exc.value.status_code == 404
    assert VALID_ID in exc.value.detail


@pytest.mark.asyncio
async def test_get_course_invalid_id_returns_404(service):
    with pytest.raises(HTTPException) as exc:
        await service.get_course("not-a-real-id")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_list_courses(service):
    await service.create_course(make_course_data(title="Course One Title"))
    await service.create_course(make_course_data(title="Course Two Title"))

    courses = await service.list_courses()

    assert len(courses) == 2
    titles = {c["title"] for c in courses}
    assert titles == {"Course One Title", "Course Two Title"}


@pytest.mark.asyncio
async def test_list_courses_respects_limit(service):
    for index in range(5):
        await service.create_course(make_course_data(title=f"Course Number {index}"))

    assert len(await service.list_courses(limit=3)) == 3


@pytest.mark.asyncio
async def test_update_course_partial_fields_only(service):
    created = await service.create_course(make_course_data())

    updated = await service.update_course(
        created["id"], CourseUpdate(title="Renamed Course Title")
    )

    assert updated["title"] == "Renamed Course Title"
    assert updated["category"] == "programming"  # untouched field stays
    assert updated["tags"] == ["python", "beginner"]


@pytest.mark.asyncio
async def test_update_course_not_found(service):
    with pytest.raises(HTTPException) as exc:
        await service.update_course(VALID_ID, CourseUpdate(title="Ghost Course Name"))
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_course(service):
    created = await service.create_course(make_course_data())

    await service.delete_course(created["id"])

    with pytest.raises(HTTPException):
        await service.get_course(created["id"])


@pytest.mark.asyncio
async def test_delete_course_not_found(service):
    with pytest.raises(HTTPException) as exc:
        await service.delete_course(VALID_ID)
    assert exc.value.status_code == 404
