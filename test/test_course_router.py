"""API tests for /courses (public router - no auth required)."""

import pytest

MISSING_ID = "64b1f0c0a1b2c3d4e5f60718"


@pytest.fixture
def create_course(api, course_payload):
    def _create(**overrides) -> dict:
        payload = {**course_payload, **overrides}
        response = api.post("/courses/", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _create


def test_create_course_returns_201(create_course):
    course = create_course()
    assert course["id"]
    assert course["title"] == "Python 101 Basics"
    assert course["instructor_id"] == "instructor-1"
    assert course["created_at"]


def test_create_course_validation_error(api):
    response = api.post(
        "/courses/",
        json={"title": "abc", "instructor_id": "i", "category": "c"},  # title < 5
    )
    assert response.status_code == 422


def test_list_courses(api, create_course):
    create_course(title="Course One Title")
    create_course(title="Course Two Title")

    response = api.get("/courses/")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_course_by_id(api, create_course):
    course = create_course()

    response = api.get(f"/courses/{course['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == course["id"]


def test_get_missing_course_returns_404(api):
    response = api.get(f"/courses/{MISSING_ID}")
    assert response.status_code == 404


def test_update_course(api, create_course):
    course = create_course()

    response = api.put(f"/courses/{course['id']}", json={"title": "Updated Course Name"})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Updated Course Name"
    assert body["category"] == "programming"  # untouched field stays


def test_update_missing_course_returns_404(api):
    response = api.put(f"/courses/{MISSING_ID}", json={"title": "Ghost Course Name"})
    assert response.status_code == 404


def test_delete_course(api, create_course):
    course = create_course()

    response = api.delete(f"/courses/{course['id']}")

    assert response.status_code == 200
    assert response.json()["message"] == "Course deleted successfully"
    assert api.get(f"/courses/{course['id']}").status_code == 404


def test_delete_missing_course_returns_404(api):
    response = api.delete(f"/courses/{MISSING_ID}")
    assert response.status_code == 404
