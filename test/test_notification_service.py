"""Unit tests for NotificationService (WebSocket push is mocked)."""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from services.notification_service import NotificationService


@pytest.fixture
def mock_send(monkeypatch):
    """Capture realtime pushes instead of touching real WebSockets."""
    from services import notification_service

    send_mock = AsyncMock()
    monkeypatch.setattr(
        notification_service.connection_manager, "send_to_user", send_mock
    )
    return send_mock


@pytest.fixture
def service(fake_db, mock_send) -> NotificationService:
    return NotificationService()


@pytest.mark.asyncio
async def test_create_notification_persists_and_pushes(service, mock_send):
    notification = await service.create_notification(
        user_id="user-1",
        title="Welcome",
        message="Hello!",
        notification_type="success",
        data={"course": "Python 101"},
    )

    assert notification["user_id"] == "user-1"
    assert notification["title"] == "Welcome"
    assert notification["message"] == "Hello!"
    assert notification["type"] == "success"
    assert notification["read"] is False
    assert notification["data"] == {"course": "Python 101"}
    assert notification["id"]
    assert notification["created_at"]

    mock_send.assert_awaited_once()
    user_id, payload = mock_send.await_args.args
    assert user_id == "user-1"
    assert payload["type"] == "notification"
    assert payload["data"]["title"] == "Welcome"


@pytest.mark.asyncio
async def test_create_notification_applies_defaults(service, mock_send):
    notification = await service.create_notification("user-1", "T", "M")
    assert notification["type"] == "info"
    assert notification["data"] == {}
    assert notification["read"] is False


@pytest.mark.asyncio
async def test_list_notifications_returns_only_own(service):
    for user in ("user-1", "user-1", "user-2"):
        await service.create_notification(user, "T", "M")

    notifications = await service.list_notifications("user-1")

    assert len(notifications) == 2
    assert all(n["user_id"] == "user-1" for n in notifications)


@pytest.mark.asyncio
async def test_list_notifications_unread_only_and_limit(service):
    for _ in range(3):
        await service.create_notification("user-1", "T", "M")
    await service.mark_all_read("user-1")
    await service.create_notification("user-1", "New", "M")

    unread = await service.list_notifications("user-1", unread_only=True)
    assert len(unread) == 1
    assert unread[0]["title"] == "New"

    limited = await service.list_notifications("user-1", limit=2)
    assert len(limited) == 2


@pytest.mark.asyncio
async def test_unread_count(service):
    for _ in range(2):
        await service.create_notification("user-1", "T", "M")
    await service.create_notification("user-2", "T", "M")

    assert await service.unread_count("user-1") == 2

    await service.mark_all_read("user-1")
    assert await service.unread_count("user-1") == 0


@pytest.mark.asyncio
async def test_get_notification(service):
    created = await service.create_notification("user-1", "T", "M")
    fetched = await service.get_notification(created["id"])
    assert fetched["id"] == created["id"]
    assert fetched["title"] == "T"


@pytest.mark.asyncio
async def test_get_notification_not_found(service):
    with pytest.raises(HTTPException) as exc:
        await service.get_notification("64b1f0c0a1b2c3d4e5f60718")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_mark_read(service):
    created = await service.create_notification("user-1", "T", "M")
    assert created["read"] is False

    updated = await service.mark_read(created["id"])

    assert updated["read"] is True
    assert await service.unread_count("user-1") == 0


@pytest.mark.asyncio
async def test_mark_read_not_found(service):
    with pytest.raises(HTTPException) as exc:
        await service.mark_read("64b1f0c0a1b2c3d4e5f60718")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_mark_all_read_returns_modified_count(service):
    for _ in range(3):
        await service.create_notification("user-1", "T", "M")

    assert await service.mark_all_read("user-1") == 3
    assert await service.mark_all_read("user-1") == 0  # nothing left to mark


@pytest.mark.asyncio
async def test_delete_notification(service):
    created = await service.create_notification("user-1", "T", "M")

    await service.delete_notification(created["id"])

    assert await service.list_notifications("user-1") == []


@pytest.mark.asyncio
async def test_delete_notification_not_found(service):
    with pytest.raises(HTTPException) as exc:
        await service.delete_notification("64b1f0c0a1b2c3d4e5f60718")
    assert exc.value.status_code == 404
