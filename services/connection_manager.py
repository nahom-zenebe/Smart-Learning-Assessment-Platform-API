from collections import defaultdict
from typing import Dict, Set

from fastapi import WebSocket


class ConnectionManager:
    """In-memory hub of active WebSocket connections, keyed by user_id."""

    def __init__(self) -> None:
        self.active: Dict[str, Set[WebSocket]] = defaultdict(set)
        self.user_infos: Dict[str, dict] = {}

    async def connect(self, user_id: str, user_info: dict, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active[user_id].add(websocket)
        self.user_infos[user_id] = user_info

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        conns = self.active.get(user_id)
        if conns:
            conns.discard(websocket)
            if not conns:
                self.active.pop(user_id, None)
                self.user_infos.pop(user_id, None)

    async def send_to_user(self, user_id: str, payload: dict) -> None:
        """Push a JSON payload to every socket of a user (best-effort)."""
        for websocket in list(self.active.get(user_id, ())):
            try:
                await websocket.send_json(payload)
            except Exception:
                # Socket is gone; drop it silently.
                self.disconnect(user_id, websocket)

    async def broadcast(self, payload: dict) -> None:
        for user_id in list(self.active.keys()):
            await self.send_to_user(user_id, payload)

    def connected_count(self) -> int:
        return sum(len(conns) for conns in self.active.values())


connection_manager = ConnectionManager()