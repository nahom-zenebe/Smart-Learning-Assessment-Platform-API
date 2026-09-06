"""Shared test fixtures for the notification / course / quiz / question tests.

No real MongoDB or WebSocket connections are needed: repositories resolve the
database through ``db.mongodb.get_database()`` at call time, so tests simply
swap the module-level ``db`` handle for an in-memory fake.
"""

import os
import sys
from copy import deepcopy
from types import SimpleNamespace
from typing import Dict, List, Optional

from bson import ObjectId

# Make the project root importable regardless of where pytest is launched.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from db import mongodb


# ---------------------------------------------------------------------------
# In-memory fake covering the small subset of Motor/PyMongo used by repos
# ---------------------------------------------------------------------------
def _matches(doc: dict, query: dict) -> bool:
    return all(doc.get(key) == value for key, value in query.items())


class FakeCursor:
    """Emulates ``find(...).sort(...).limit(...)`` and ``await to_list()``."""

    def __init__(self, docs: List[dict]):
        self._docs = docs
        self._sort_key = "_id"
        self._direction = 1
        self._limit: Optional[int] = None

    def sort(self, key: str, direction: int) -> "FakeCursor":
        self._sort_key, self._direction = key, direction
        return self

    def limit(self, count: int) -> "FakeCursor":
        self._limit = count
        return self

    async def to_list(self, length: Optional[int] = None) -> List[dict]:
        docs = sorted(
            self._docs,
            key=lambda d: d.get(self._sort_key),
            reverse=self._direction < 0,
        )
        cap = self._limit if self._limit is not None else length
        if cap is not None:
            docs = docs[:cap]
        return deepcopy(docs)


class FakeCollection:
    def __init__(self) -> None:
        self._docs: List[dict] = []

    async def insert_one(self, doc: dict):
        stored = deepcopy(dict(doc))
        if not stored.get("_id"):
            stored["_id"] = ObjectId()
        self._docs.append(stored)
        return SimpleNamespace(inserted_id=stored["_id"])

    async def find_one(self, query: dict) -> Optional[dict]:
        for doc in self._docs:
            if _matches(doc, query):
                return deepcopy(doc)
        return None

    def find(self, query: dict) -> FakeCursor:
        return FakeCursor([d for d in self._docs if _matches(d, query)])

    async def count_documents(self, query: dict) -> int:
        return sum(1 for d in self._docs if _matches(d, query))

    async def update_one(self, query: dict, update: dict):
        for doc in self._docs:
            if _matches(doc, query):
                self._apply(doc, update)
                return SimpleNamespace(matched_count=1, modified_count=1)
        return SimpleNamespace(matched_count=0, modified_count=0)

    async def update_many(self, query: dict, update: dict):
        modified = 0
        for doc in self._docs:
            if _matches(doc, query):
                before = deepcopy(doc)
                self._apply(doc, update)
                if before != doc:
                    modified += 1
        return SimpleNamespace(matched_count=modified, modified_count=modified)

    async def delete_one(self, query: dict):
        for index, doc in enumerate(self._docs):
            if _matches(doc, query):
                del self._docs[index]
                return SimpleNamespace(deleted_count=1)
        return SimpleNamespace(deleted_count=0)

    @staticmethod
    def _apply(doc: dict, update: dict) -> None:
        if "$set" in update:
            for key, value in update["$set"].items():
                doc[key] = deepcopy(value)
        if "$addToSet" in update:
            for key, value in update["$addToSet"].items():
                doc.setdefault(key, [])
                if value not in doc[key]:
                    doc[key].append(value)
        if "$pull" in update:
            for key, value in update["$pull"].items():
                if isinstance(doc.get(key), list):
                    doc[key] = [item for item in doc[key] if item != value]


class FakeDatabase:
    """``client[db_name]``-style mapping that creates collections on demand."""

    def __init__(self) -> None:
        self._collections: Dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        if name not in self._collections:
            self._collections[name] = FakeCollection()
        return self._collections[name]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def fake_db(monkeypatch) -> FakeDatabase:
    """Swap the shared Mongo handle for a fresh in-memory fake per test."""
    database = FakeDatabase()
    monkeypatch.setattr(mongodb, "db", database)
    return database


class FakeAuthMiddleware:
    """Injects a fake user into ``request.scope`` from test headers.

    Mirrors what ``JWTAuthMiddleware`` does in production, so the real
    ``get_current_user`` / ``require_roles`` dependencies are exercised.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = {
                key.decode().lower(): value.decode()
                for key, value in scope.get("headers", [])
            }
            user_id = headers.get("x-test-user-id")
            if user_id:
                scope["user"] = {
                    "id": user_id,
                    "role": headers.get("x-test-role", "student"),
                    "email": f"{user_id}@example.com",
                }
        await self.app(scope, receive, send)


@pytest.fixture
def api(fake_db) -> TestClient:
    """Test app including only the routers under test (no real middleware)."""
    from router.course_router import router as course_router
    from router.notification_router import router as notification_router
    from router.question_router import router as question_router
    from router.quiz_router import router as quiz_router

    app = FastAPI()
    app.add_middleware(FakeAuthMiddleware)
    app.include_router(course_router)
    app.include_router(quiz_router)
    app.include_router(question_router)
    app.include_router(notification_router)
    return TestClient(app)


# ---------------------------------------------------------------------------
# Payload builders shared by service and router tests
# ---------------------------------------------------------------------------
@pytest.fixture
def course_payload() -> dict:
    return {
        "title": "Python 101 Basics",
        "description": "Intro to Python programming",
        "instructor_id": "instructor-1",
        "category": "programming",
        "tags": ["python", "beginner"],
        "lessons": [],
    }


@pytest.fixture
def quiz_payload() -> dict:
    return {
        "lesson_id": "lesson-1",
        "title": "Chapter 1 Quiz",
        "description": "Covers chapter 1",
        "questions": [],
    }


@pytest.fixture
def make_question_payload():
    def _build(quiz_id: str, **overrides) -> dict:
        payload = {
            "quiz_id": quiz_id,
            "text": "What is 2 + 2?",
            "options": ["3", "4", "5"],
            "correct_option_id": "1",
        }
        payload.update(overrides)
        return payload

    return _build

