from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from models.objectid import PyObjectId
from models.Question import utcnow


class SubmissionBase(BaseModel):
    quiz_id: str
    user_id: str
    answers: List[str] = []  # one chosen option index (as string) per question


class SubmissionCreate(SubmissionBase):
    pass


class Submission(SubmissionBase):
    id: Optional[PyObjectId] = None
    score: float = 0.0  # percentage 0-100, computed server-side
    submitted_at: datetime = Field(default_factory=utcnow)

    model_config = ConfigDict(populate_by_name=True)
