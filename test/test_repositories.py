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
