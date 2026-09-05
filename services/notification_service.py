from typing import List, Optional

from fastapi import HTTPException, status

from models.Notification import NotificationCreate
from models.Question import utcnow
from repositories.notification_repository import NotificationRepository
from services.connection_manager import connection_manager


class NotificationService:
    def __init__(self):
        self.repo = NotificationRepository()

    async def create_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: str = "info",
        data: Optional[dict] = None,
    ) -> dict:
        """Persist a notification and push it live to the user if connected."""
        payload = NotificationCreate(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            data=data or {},
        ).model_dump()
        payload["read"] = False
        payload["created_at"] = utcnow()

        notification_id = await self.repo.create(payload)
        notification = await self.repo.get_by_id(notification_id)

        await connection_manager.send_to_user(
            user_id, {"type": "notification", "data": notification}
        )
        return notification

    async def list_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[dict]:
        return await self.repo.list_for_user(
            user_id, unread_only=unread_only, limit=min(limit, 200)
        )

    async def unread_count(self, user_id: str) -> int:
        return await self.repo.unread_count(user_id)

    async def get_notification(self, notification_id: str) -> dict:
        notification = await self.repo.get_by_id(notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification {notification_id} not found",
            )
        return notification

    async def mark_read(self, notification_id: str) -> dict:
        notification = await self.repo.mark_read(notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification {notification_id} not found",
            )
        return notification

    async def mark_all_read(self, user_id: str) -> int:
        return await self.repo.mark_all_read(user_id)

    async def delete_notification(self, notification_id: str) -> None:
        if not await self.repo.delete(notification_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification {notification_id} not found",
            )