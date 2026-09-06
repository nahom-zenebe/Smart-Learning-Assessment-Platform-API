"""Pydantic model tests for notification, course, quiz and question."""

import pytest
from bson import ObjectId
from pydantic import ValidationError

from models.Course import Course, CourseCreate, CourseUpdate
from models.Notification import Notification, NotificationCreate, NotificationUpdate
from models.Question import Question, QuestionCreate, QuestionUpdate, utcnow
from models.Quiz import Quiz, QuizCreate, QuizUpdate
from models.objectid import PyObjectId

VALID_OBJECT_ID = "64b1f0c0a1b2c3d4e5f60718"


class TestNotificationModels:
    def test_create_defaults(self):
        notification = NotificationCreate(user_id="user-1", title="Hi", message="Hello")
        assert notification.type == "info"
        assert notification.data is None

    def test_create_full_payload(self):
        notification = NotificationCreate(
            user_id="user-1",
            title="Grade posted",
            message="You passed",
            type="grade",
            data={"score": 90},
        )
        assert notification.type == "grade"
        assert notification.data == {"score": 90}

    def test_notification_defaults(self):
        notification = Notification(user_id="u", title="t", message="m")
        assert notification.read is False
        assert notification.created_at is not None
        assert notification.created_at.tzinfo is not None  # timezone-aware

    def test_id_accepts_object_id_string_and_serializes_back(self):
        notification = Notification(
            id=VALID_OBJECT_ID, user_id="u", title="t", message="m"
        )
        assert notification.id == ObjectId(VALID_OBJECT_ID)
        assert notification.model_dump(mode="json")["id"] == VALID_OBJECT_ID

    def test_update_partial_dump(self):
        assert NotificationUpdate(read=True).model_dump(exclude_unset=True) == {
            "read": True
        }
        assert NotificationUpdate().model_dump(exclude_unset=True) == {}

    @pytest.mark.parametrize("missing", ["user_id", "title", "message"])
    def test_create_required_fields(self, missing):
        payload = {"user_id": "u", "title": "t", "message": "m"}
        payload.pop(missing)
        with pytest.raises(ValidationError):
            NotificationCreate(**payload)


class TestCourseModels:
    def test_create_defaults(self):
        course = CourseCreate(
            title="Python 101 Basics", instructor_id="inst-1", category="programming"
        )
        assert course.description is None
        assert course.tags == []
        assert course.lessons == []

    def test_title_min_length_enforced(self):
        with pytest.raises(ValidationError):
            CourseCreate(title="abc", instructor_id="i", category="c")

    def test_title_exactly_five_chars_is_valid(self):
        course = CourseCreate(title="abcde", instructor_id="i", category="c")
        assert course.title == "abcde"

    def test_created_at_default_is_timezone_aware(self):
        course = Course(title="Python 101 Basics", instructor_id="i", category="c")
        assert course.created_at.tzinfo is not None

    def test_update_all_fields_optional(self):
        assert CourseUpdate().model_dump(exclude_unset=True) == {}
        update = CourseUpdate(title="New Title Here", tags=["python"])
        assert update.model_dump(exclude_unset=True) == {
            "title": "New Title Here",
            "tags": ["python"],
        }


class TestQuizModels:
    def test_create_defaults(self):
        quiz = QuizCreate(lesson_id="lesson-1", title="Chapter 1 Quiz")
        assert quiz.description is None
        assert quiz.questions == []

    def test_lesson_id_is_required(self):
        with pytest.raises(ValidationError):
            QuizCreate(title="Quiz without lesson")

    def test_update_partial_dump(self):
        assert QuizUpdate(title="Renamed").model_dump(exclude_unset=True) == {
            "title": "Renamed"
        }

    def test_created_at_default(self):
        quiz = Quiz(lesson_id="l", title="t")
        assert quiz.created_at.tzinfo is not None


class TestQuestionModels:
    def test_create(self):
        question = QuestionCreate(
            quiz_id="quiz-1", text="2+2?", options=["3", "4"], correct_option_id="1"
        )
        assert question.options == ["3", "4"]
        assert question.correct_option_id == "1"

    def test_options_default_to_empty(self):
        question = QuestionCreate(quiz_id="q", text="t", correct_option_id="0")
        assert question.options == []

    def test_correct_option_id_is_required(self):
        with pytest.raises(ValidationError):
            QuestionCreate(quiz_id="q", text="t", options=["a"])

    def test_update_partial_dump(self):
        assert QuestionUpdate(text="new").model_dump(exclude_unset=True) == {
            "text": "new"
        }

    def test_created_at_default(self):
        question = Question(quiz_id="q", text="t", correct_option_id="0")
        assert question.created_at.tzinfo is not None


class TestPyObjectId:
    def test_accepts_valid_hex_string(self):
        assert PyObjectId.validate(VALID_OBJECT_ID) == ObjectId(VALID_OBJECT_ID)

    def test_accepts_object_id_instance(self):
        object_id = ObjectId()
        assert PyObjectId.validate(object_id) is object_id

    def test_rejects_invalid_string(self):
        with pytest.raises(ValueError):
            PyObjectId.validate("not-an-object-id")

    def test_serializes_to_string_inside_model(self):
        question = Question(
            id=VALID_OBJECT_ID, quiz_id="q", text="t", correct_option_id="0"
        )
        assert question.model_dump(mode="json")["id"] == VALID_OBJECT_ID


def test_utcnow_is_timezone_aware_utc():
    now = utcnow()
    assert now.tzinfo is not None
    assert now.utcoffset().total_seconds() == 0
