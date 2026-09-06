"""API tests for /questions (public router - no auth required)."""

import pytest

MISSING_ID = "64b1f0c0a1b2c3d4e5f60718"


@pytest.fixture
def create_quiz(api, quiz_payload):
    def _create() -> dict:
        response = api.post("/quizzes/", json=quiz_payload)
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


def test_create_question_returns_201_and_links_quiz(api, create_quiz, create_question):
    quiz = create_quiz()

    question = create_question(quiz["id"])

    assert question["id"]
    assert question["quiz_id"] == quiz["id"]
    assert question["correct_option_id"] == "1"

    # the question id was pushed into the quiz's question list
    quiz_questions = api.get(f"/quizzes/{quiz['id']}/questions").json()
    assert [q["id"] for q in quiz_questions] == [question["id"]]


def test_create_question_for_missing_quiz_returns_404(api, make_question_payload):
    response = api.post("/questions/", json=make_question_payload(MISSING_ID))
    assert response.status_code == 404


def test_create_question_invalid_correct_option_returns_400(
    api, create_quiz, make_question_payload
):
    quiz = create_quiz()
    response = api.post(
        "/questions/", json=make_question_payload(quiz["id"], correct_option_id="9")
    )
    assert response.status_code == 400


def test_create_question_missing_required_field_returns_422(
    api, create_quiz, make_question_payload
):
    quiz = create_quiz()
    payload = make_question_payload(quiz["id"])
    payload.pop("correct_option_id")

    response = api.post("/questions/", json=payload)

    assert response.status_code == 422


def test_list_questions(api, create_quiz, create_question):
    quiz = create_quiz()
    create_question(quiz["id"], text="First question")
    create_question(quiz["id"], text="Second question")

    response = api.get("/questions/")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_question_by_id(api, create_quiz, create_question):
    quiz = create_quiz()
    question = create_question(quiz["id"])

    response = api.get(f"/questions/{question['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == question["id"]


def test_get_missing_question_returns_404(api):
    response = api.get(f"/questions/{MISSING_ID}")
    assert response.status_code == 404


def test_update_question(api, create_quiz, create_question):
    quiz = create_quiz()
    question = create_question(quiz["id"])

    response = api.put(
        f"/questions/{question['id']}", json={"text": "Updated question text"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "Updated question text"
    assert body["correct_option_id"] == "1"  # untouched field stays


def test_update_missing_question_returns_404(api):
    response = api.put(f"/questions/{MISSING_ID}", json={"text": "Ghost question"})
    assert response.status_code == 404


def test_delete_question_unlinks_from_quiz(api, create_quiz, create_question):
    quiz = create_quiz()
    question = create_question(quiz["id"])

    response = api.delete(f"/questions/{question['id']}")

    assert response.status_code == 200
    assert response.json()["message"] == "Question deleted successfully"

    assert api.get(f"/questions/{question['id']}").status_code == 404
    quiz_questions = api.get(f"/quizzes/{quiz['id']}/questions").json()
    assert quiz_questions == []


def test_delete_missing_question_returns_404(api):
    response = api.delete(f"/questions/{MISSING_ID}")
    assert response.status_code == 404
