from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from jose.exceptions import JWTError

from core.security import decode_token
from models.Question import utcnow
from services.connection_manager import connection_manager
from services.notification_service import NotificationService

router = APIRouter(tags=["Notifications WebSocket"])


async def _authenticate_token(websocket: WebSocket, token: str) -> dict | None:
    """Validate the JWT from the query param (or the access_token cookie) and
    return the user claims. BaseHTTPMiddleware passes websocket scopes straight
    through, so we authenticate here instead of relying on JWTAuthMiddleware.
    """
    if not token:
        token = websocket.cookies.get("access_token", "")
    if token:
        try:
            claims = decode_token(token)
        except JWTError:
            claims = None
        if claims and claims.get("user_id"):
            return {
                "id": str(claims["user_id"]),
                "email": claims.get("sub"),
                "role": claims.get("role", "student"),
            }
    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    return None


@router.websocket("/ws/notifications")
async def ws_notifications(
    websocket: WebSocket,
    token: str = Query(default=""),
):
    """Live notification stream.

    Authenticate with ``?token=<jwt>`` (or the ``access_token`` cookie).
    On connect the server sends a ``hello`` frame carrying the user's unread
    notifications. Afterwards, notifications are pushed as:
      {"type": "notification", "data": {...notification...}}
    Clients may send ``{"type": "ping"}`` to keep the connection alive and
    receive a ``pong``.
    """
    user = await _authenticate_token(websocket, token)
    if not user:
        return

    manager = connection_manager
    user_id = user["id"]
    await manager.connect(user_id, user, websocket)

    try:
        unread = await NotificationService().list_notifications(
            user_id, unread_only=True, limit=20
        )
        await websocket.send_json(
            {
                "type": "hello",
                "user_id": user_id,
                "unread_count": len(unread),
                "notifications": unread,
            }
        )

        while True:
            try:
                data = await websocket.receive_json()
            except Exception:
                # Non-JSON payload - ignore and keep listening.
                continue

            message_type = data.get("type")
            if message_type == "ping":
                await websocket.send_json(
                    {"type": "pong", "timestamp": utcnow().isoformat()}
                )
            elif message_type == "mark_read":
                notification_id = data.get("notification_id")
                if notification_id:
                    await NotificationService().mark_read(notification_id)

    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)