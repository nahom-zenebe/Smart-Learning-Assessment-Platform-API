from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from models.Question import utcnow
from models.objectid import PyObjectId


class NotificationCreate(BaseModel):
    user_id: str
    title: str
    message: str
    type: str = "info"  # info | success | warning | grade | progress
    data: Optional[Dict[str, Any]] = None


class NotificationUpdate(BaseModel):
    read: Optional[bool] = None


class Notification(NotificationCreate):
    id: Optional[PyObjectId] = None
    read: bool = False
    created_at: datetime = Field(default_factory=utcnow)

    model_config = ConfigDict(populate_by_name=True)