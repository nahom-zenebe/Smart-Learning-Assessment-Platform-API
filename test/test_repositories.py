"""Repository tests for notification, course, quiz and question (fake MongoDB)."""

import pytest
from bson import ObjectId

from repositories.course_repository import CourseRepository
from repositories.notification_repository import NotificationRepository
from repositories.question_repository import QuestionRepository
from repositories.quiz_repository import QuizRepository

VALID_ID = "64b1f0c0a1b2c3d4e5f60718"


# ---------------------------------------------------------------------------
# NotificationRepository
# ---------------------------------------------------------------------------
class TestNotificationRepository:
    @pytest.fixture
    def repo(self, fake_db) -> NotificationRepository:
        return NotificationRepository()

    async def _insert(self, repo, user_id="user-1", read=False, **extra):
        doc = {"user_id": user_id, "title": "T", "message": "M", "read": read}
        doc.update(extra)
        return await repo.create(doc)

    @pytest.mark.asyncio
    async def test_create_returns_string_id(self, repo):
        notification_id = await repo.create({"user_id": "user-1"})
        assert isinstance(notification_id, str)
        assert ObjectId.is_valid(notification_id)

    @pytest.mark.asyncio
    async def test_get_by_id_serializes_id(self, repo):
        notification_id = await self._insert(repo)

        doc = await repo.get_by_id(notification_id)

        assert doc["id"] == notification_id  # _id renamed to id string
        assert "_id" not in doc

    @pytest.mark.asyncio
    async def test_get_by_id_missing_or_invalid(self, repo):
        assert await repo.get_by_id(VALID_ID) is None
        assert await repo.get_by_id("not-an-object-id") is None

    @pytest.mark.asyncio
    async def test_list_for_user_filters_and_sorts(self, repo):
        await self._insert(repo, user_id="user-1")
        await self._insert(repo, user_id="user-2")
        last = await self._insert(repo, user_id="user-1")

        docs = await repo.list_for_user("user-1")

        assert len(docs) == 2
        assert docs[0]["id"] == last  # newest first (_id desc)

    @pytest.mark.asyncio
    async def test_list_for_user_unread_only(self, repo):
        await self._insert(repo, read=True)
        unread = await self._insert(repo, read=False)

        docs = await repo.list_for_user("user-1", unread_only=True)

        assert [d["id"] for d in docs] == [unread]

    @pytest.mark.asyncio
    async def test_list_for_user_limit(self, repo):
        for _ in range(4):
            await self._insert(repo)
        assert len(await repo.list_for_user("user-1", limit=2)) == 2

    @pytest.mark.asyncio
    async def test_unread_count(self, repo):
        await self._insert(repo, read=True)
        await self._insert(repo, read=False)
        await self._insert(repo, user_id="user-2", read=False)

        assert await repo.unread_count("user-1") == 1

    @pytest.mark.asyncio
    async def test_mark_read(self, repo):
        notification_id = await self._insert(repo)

        doc = await repo.mark_read(notification_id)

        assert doc["read"] is True

    @pytest.mark.asyncio
    async def test_mark_read_invalid_id(self, repo):
        assert await repo.mark_read("not-an-object-id") is None

    @pytest.mark.asyncio
    async def test_mark_all_read_counts_modified(self, repo):
        for _ in range(3):
            await self._insert(repo, read=False)

        assert await repo.mark_all_read("user-1") == 3
        assert await repo.mark_all_read("user-1") == 0

    @pytest.mark.asyncio
    async def test_delete(self, repo):
        notification_id = await self._insert(repo)
        assert await repo.delete(notification_id) is True
        assert await repo.get_by_id(notification_id) is None

    @pytest.mark.asyncio
    async def test_delete_missing_or_invalid(self, repo):
        assert await repo.delete(VALID_ID) is False
        assert await repo.delete("not-an-object-id") is False


# ---------------------------------------------------------------------------
# CourseRepository
# ---------------------------------------------------------------------------
class TestCourseRepository:
    @pytest.fixture
    def repo(self, fake_db) -> CourseRepository:
        return CourseRepository()

    async def _insert(self, repo, title="Course One Title"):
        return await repo.create({"title": title, "category": "c"})

    @pytest.mark.asyncio
    async def test_create_and_get_by_id(self, repo):
        course_id = await self._insert(repo)
        doc = await repo.get_by_id(course_id)
        assert doc["id"] == course_id
        assert doc["title"] == "Course One Title"

    @pytest.mark.asyncio
    async def test_get_by_id_missing_or_invalid(self, repo):
        assert await repo.get_by_id(VALID_ID) is None
        assert await repo.get_by_id("not-an-object-id") is None

    @pytest.mark.asyncio
    async def test_list_all(self, repo):
        await self._insert(repo, title="Course One Title")
        await self._insert(repo, title="Course Two Title")
        docs = await repo.list_all()
        assert len(docs) == 2

    @pytest.mark.asyncio
    async def test_update(self, repo):
        course_id = await self._insert(repo)
        doc = await repo.update(course_id, {"title": "Renamed Course Title"})
        assert doc["title"] == "Renamed Course Title"

    @pytest.mark.asyncio
    async def test_update_invalid_id(self, repo):
        assert await repo.update("not-an-object-id", {"title": "x"}) is None

    @pytest.mark.asyncio
    async def test_delete(self, repo):
        course_id = await self._insert(repo)
        assert await repo.delete(course_id) is True
        assert await repo.get_by_id(course_id) is None

    @pytest.mark.asyncio
    async def test_delete_missing_or_invalid(self, repo):
        assert await repo.delete(VALID_ID) is False
        assert await repo.delete("not-an-object-id") is False


# ---------------------------------------------------------------------------
# QuizRepository
# ---------------------------------------------------------------------------
class TestQuizRepository:
    @pytest.fixture
    def repo(self, fake_db) -> QuizRepository:
        return QuizRepository()

    async def _insert(self, repo, title="Quiz One Title"):
        return await repo.create({"lesson_id": "lesson-1", "title": title})

    @pytest.mark.asyncio
    async def test_create_and_get_by_id(self, repo):
        quiz_id = await self._insert(repo)
        doc = await repo.get_by_id(quiz_id)
        assert doc["id"] == quiz_id
        assert doc["title"] == "Quiz One Title"

    @pytest.mark.asyncio
    async def test_get_by_id_missing_or_invalid(self, repo):
        assert await repo.get_by_id(VALID_ID) is None
        assert await repo.get_by_id("not-an-object-id") is None

    @pytest.mark.asyncio
    async def test_list_all(self, repo):
        await self._insert(repo, title="Quiz One Title")
        await self._insert(repo, title="Quiz Two Title")
        assert len(await repo.list_all()) == 2

    @pytest.mark.asyncio
    async def test_update(self, repo):
        quiz_id = await self._insert(repo)
        doc = await repo.update(quiz_id, {"title": "Renamed Quiz Title"})
        assert doc["title"] == "Renamed Quiz Title"

    @pytest.mark.asyncio
    async def test_update_invalid_id(self, repo):
        assert await repo.update("not-an-object-id", {"title": "x"}) is None

    @pytest.mark.asyncio
    async def test_delete(self, repo):
        quiz_id = await self._insert(repo)
        assert await repo.delete(quiz_id) is True
        assert await repo.get_by_id(quiz_id) is None

    @pytest.mark.asyncio
    async def test_delete_missing_or_invalid(self, repo):
        assert await repo.delete(VALID_ID) is False
        assert await repo.delete("not-an-object-id") is False

    @pytest.mark.asyncio
    async def test_push_question_adds_without_duplicates(self, repo):
        quiz_id = await self._insert(repo)

        await repo.push_question(quiz_id, "question-1")
        await repo.push_question(quiz_id, "question-1")  # duplicate ignored
        await repo.push_question(quiz_id, "question-2")

        doc = await repo.get_by_id(quiz_id)
        assert doc["questions"] == ["question-1", "question-2"]

    @pytest.mark.asyncio
    async def test_pull_question_removes_only_target(self, repo):
        quiz_id = await self._insert(repo)
        await repo.push_question(quiz_id, "question-1")
        await repo.push_question(quiz_id, "question-2")

        await repo.pull_question(quiz_id, "question-1")

        doc = await repo.get_by_id(quiz_id)
        assert doc["questions"] == ["question-2"]

    @pytest.mark.asyncio
    async def test_push_and_pull_invalid_quiz_id_are_noops(self, repo):
        await repo.push_question("not-an-object-id", "question-1")  # no raise
        await repo.pull_question("not-an-object-id", "question-1")  # no raise


# ---------------------------------------------------------------------------
# QuestionRepository
# ---------------------------------------------------------------------------
class TestQuestionRepository:
    @pytest.fixture
    def repo(self, fake_db) -> QuestionRepository:
        return QuestionRepository()

    async def _insert(self, repo, quiz_id="quiz-1", text="Question text"):
        return await repo.create(
            {
                "quiz_id": quiz_id,
                "text": text,
                "options": ["a"],
                "correct_option_id": "0",
            }
        )

    @pytest.mark.asyncio
    async def test_create_and_get_by_id(self, repo):
        question_id = await self._insert(repo)
        doc = await repo.get_by_id(question_id)
        assert doc["id"] == question_id
        assert doc["text"] == "Question text"

    @pytest.mark.asyncio
    async def test_get_by_id_missing_or_invalid(self, repo):
        assert await repo.get_by_id(VALID_ID) is None
        assert await repo.get_by_id("not-an-object-id") is None

    @pytest.mark.asyncio
    async def test_get_by_quiz_returns_creation_order(self, repo):
        quiz_id = "quiz-abc"
        first = await self._insert(repo, quiz_id=quiz_id, text="First question")
        second = await self._insert(repo, quiz_id=quiz_id, text="Second question")
        await self._insert(repo, quiz_id="other-quiz", text="Other question")

        docs = await repo.get_by_quiz(quiz_id)

        assert [d["id"] for d in docs] == [first, second]

    @pytest.mark.asyncio
    async def test_get_by_quiz_empty_for_unknown_quiz(self, repo):
        assert await repo.get_by_quiz(VALID_ID) == []

    @pytest.mark.asyncio
    async def test_update(self, repo):
        question_id = await self._insert(repo)
        doc = await repo.update(question_id, {"text": "Renamed question text"})
        assert doc["text"] == "Renamed question text"

    @pytest.mark.asyncio
    async def test_update_invalid_id(self, repo):
        assert await repo.update("not-an-object-id", {"text": "x"}) is None

    @pytest.mark.asyncio
    async def test_delete(self, repo):
        question_id = await self._insert(repo)
        assert await repo.delete(question_id) is True
        assert await repo.get_by_id(question_id) is None

    @pytest.mark.asyncio
    async def test_delete_missing_or_invalid(self, repo):
        assert await repo.delete(VALID_ID) is False
        assert await repo.delete("not-an-object-id") is False
