from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from models.objectid import PyObjectId
from models.Question import utcnow


class LessonBase(BaseModel):
    course_id: str
    title: str
    content: str
    quizzes: List[str] = []


class LessonCreate(LessonBase):
    pass


class LessonUpdate(BaseModel):
    course_id: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    quizzes: Optional[List[str]] = None


class Lesson(LessonBase):
    id: Optional[PyObjectId] = None
    created_at: datetime = Field(default_factory=utcnow)

    model_config = ConfigDict(populate_by_name=True)
