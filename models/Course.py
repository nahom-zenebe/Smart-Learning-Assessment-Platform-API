from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from models.objectid import PyObjectId
from models.Question import utcnow


class CourseBase(BaseModel):
    title: str = Field(..., min_length=5)
    description: Optional[str] = None
    instructor_id: str
    category: str
    tags: List[str] = []
    lessons: List[str] = []


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5)
    description: Optional[str] = None
    instructor_id: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    lessons: Optional[List[str]] = None


class Course(CourseBase):
    id: Optional[PyObjectId] = None
    created_at: datetime = Field(default_factory=utcnow)

    model_config = ConfigDict(populate_by_name=True)


