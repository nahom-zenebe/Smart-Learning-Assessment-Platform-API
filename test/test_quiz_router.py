"""API tests for /quizzes (public router - no auth required)."""

import pytest

MISSING_ID = "64b1f0c0a1b2c3d4e5f60718"


@pytest.fixture
def create_quiz(api, quiz_payload):
    def _create(**overrides) -> dict:
        response = api.post("/quizzes/", json={**quiz_payload, **overrides})
        assert response.status_code == 201, response.text
        return response.json()

    return _create


@pytest.fixture
def create_question(api, make_question_payload):
    def _create(quiz_id: str, **overrides) -> dict:
        response = api.post(
            "/questions/", json=make_question_payload(quiz_id, **overrides)
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _create


def test_create_quiz_returns_201(create_quiz):
    quiz = create_quiz()
    assert quiz["id"]
    assert quiz["title"] == "Chapter 1 Quiz"
    assert quiz["questions"] == []
    assert quiz["created_at"]


def test_create_quiz_validation_error(api):
    response = api.post("/quizzes/", json={"title": "No lesson id"})
    assert response.status_code == 422


def test_list_quizzes(api, create_quiz):
    create_quiz(title="Quiz One Title")
    create_quiz(title="Quiz Two Title")

    response = api.get("/quizzes/")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_quiz_by_id(api, create_quiz):
    quiz = create_quiz()

    response = api.get(f"/quizzes/{quiz['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == quiz["id"]


def test_get_missing_quiz_returns_404(api):
    response = api.get(f"/quizzes/{MISSING_ID}")
    assert response.status_code == 404


def test_get_quiz_questions(api, create_quiz, create_question):
    quiz = create_quiz()
    first = create_question(quiz["id"], text="First question")
    create_question(quiz["id"], text="Second question")

    response = api.get(f"/quizzes/{quiz['id']}/questions")

    assert response.status_code == 200
    questions = response.json()
    assert len(questions) == 2
    assert questions[0]["id"] == first["id"]  # creation order preserved
    assert questions[0]["text"] == "First question"


def test_get_questions_of_missing_quiz_returns_404(api):
    response = api.get(f"/quizzes/{MISSING_ID}/questions")
    assert response.status_code == 404


def test_update_quiz(api, create_quiz):
    quiz = create_quiz()

    response = api.put(f"/quizzes/{quiz['id']}", json={"title": "Renamed Quiz Title"})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Renamed Quiz Title"
    assert body["lesson_id"] == "lesson-1"  # untouched field stays


def test_update_missing_quiz_returns_404(api):
    response = api.put(f"/quizzes/{MISSING_ID}", json={"title": "Ghost Quiz Title"})
    assert response.status_code == 404


def test_delete_quiz(api, create_quiz):
    quiz = create_quiz()

    response = api.delete(f"/quizzes/{quiz['id']}")

    assert response.status_code == 200
    assert response.json()["message"] == "Quiz deleted successfully"
    assert api.get(f"/quizzes/{quiz['id']}").status_code == 404


def test_delete_missing_quiz_returns_404(api):
    response = api.delete(f"/quizzes/{MISSING_ID}")
    assert response.status_code == 404
