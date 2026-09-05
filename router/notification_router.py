from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from core.security import get_current_user, require_roles
from models.Notification import Notification, NotificationCreate
from services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])
service = NotificationService()


@router.get(
    "/", response_model=List[Notification], status_code=status.HTTP_200_OK
)
async def list_notifications(
    unread_only: bool = False,
    limit: int = 50,
    user: dict = Depends(get_current_user),
):
    """List the authenticated user's notifications (latest first)."""
    return await service.list_notifications(
        str(user.get("id")), unread_only=unread_only, limit=limit
    )


@router.get("/unread-count", status_code=status.HTTP_200_OK)
async def unread_notifications_count(user: dict = Depends(get_current_user)):
    """Number of unread notifications for the authenticated user."""
    return {"count": await service.unread_count(str(user.get("id")))}


@router.patch("/read-all", status_code=status.HTTP_200_OK)
async def mark_all_read(user: dict = Depends(get_current_user)):
    """Mark every notification of the authenticated user as read."""
    modified = await service.mark_all_read(str(user.get("id")))
    return {"modified": modified}


@router.post(
    "/",
    response_model=Notification,
    status_code=status.HTTP_201_CREATED,
)
async def create_notification(
    payload: NotificationCreate,
    _: dict = Depends(require_roles("instructor", "admin")),
):
    """Send a notification to a user (instructors/admins only).

    The notification is persisted and, if the recipient is connected via the
    WebSocket, delivered in real time.
    """
    return await service.create_notification(
        user_id=payload.user_id,
        title=payload.title,
        message=payload.message,
        notification_type=payload.type,
        data=payload.data,
    )


@router.get(
    "/{notification_id}",
    response_model=Notification,
    status_code=status.HTTP_200_OK,
)
async def get_notification(
    notification_id: str, user: dict = Depends(get_current_user)
):
    notification = await service.get_notification(notification_id)
    _guard_owner(user, notification)
    return notification


@router.patch(
    "/{notification_id}/read",
    response_model=Notification,
    status_code=status.HTTP_200_OK,
)
async def mark_read(
    notification_id: str, user: dict = Depends(get_current_user)
):
    notification = await service.get_notification(notification_id)
    _guard_owner(user, notification)
    return await service.mark_read(notification_id)


@router.delete("/{notification_id}", status_code=status.HTTP_200_OK)
async def delete_notification(
    notification_id: str, user: dict = Depends(get_current_user)
):
    notification = await service.get_notification(notification_id)
    _guard_owner(user, notification)
    await service.delete_notification(notification_id)
    return {"message": "Notification deleted successfully", "id": notification_id}


def _guard_owner(user: dict, notification: dict) -> None:
    """Users can only manage their own notifications (admins manage all)."""
    if user.get("role") != "admin" and str(notification.get("user_id")) != str(
        user.get("id")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another user's notification",
        )