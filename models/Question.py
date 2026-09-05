from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from models.objectid import PyObjectId


def utcnow() -> datetime:
    """Timezone-aware UTC now (datetime.utcnow is deprecated in 3.12)."""
    return datetime.now(timezone.utc)


class QuestionBase(BaseModel):
    quiz_id: str
    text: str
    options: List[str] = []
    correct_option_id: str  # index (as string) of the correct option, e.g. "0"


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    quiz_id: Optional[str] = None
    text: Optional[str] = None
    options: Optional[List[str]] = None
    correct_option_id: Optional[str] = None


class Question(QuestionBase):
    id: Optional[PyObjectId] = None
    created_at: datetime = Field(default_factory=utcnow)

    model_config = ConfigDict(populate_by_name=True)
