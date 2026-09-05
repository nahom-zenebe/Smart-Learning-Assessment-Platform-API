from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from models.objectid import PyObjectId
from models.Question import utcnow


class ProgressBase(BaseModel):
    user_id: str
    course_id: str
    completed_lessons: int = 0
    total_lessons: int = 0


class ProgressCreate(ProgressBase):
    pass


class ProgressUpdate(BaseModel):
    user_id: Optional[str] = None
    course_id: Optional[str] = None
    completed_lessons: Optional[int] = None
    total_lessons: Optional[int] = None


class Progress(ProgressBase):
    id: Optional[PyObjectId] = None
    last_updated: datetime = Field(default_factory=utcnow)

    model_config = ConfigDict(populate_by_name=True)
