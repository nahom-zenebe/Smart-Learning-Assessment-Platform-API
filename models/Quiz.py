from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from models.objectid import PyObjectId
from models.Question import utcnow


class QuizBase(BaseModel):
    lesson_id: str
    title: str
    description: Optional[str] = None
    questions: List[str] = []  # linked question ids (managed by QuestionService)


class QuizCreate(QuizBase):
    pass


class QuizUpdate(BaseModel):
    lesson_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    questions: Optional[List[str]] = None


class Quiz(QuizBase):
    id: Optional[PyObjectId] = None
    created_at: datetime = Field(default_factory=utcnow)

    model_config = ConfigDict(populate_by_name=True)

