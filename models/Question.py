from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from models.objectid import PyObjectId


def utcnow() -> datetime:
    """Timezone-aware UTC now (datetime.utcnow is deprecatedin 3.12)."""
    return datetime.now(timezone.utc)


class QuestionType(str, Enum):
    """Supported assessment question types."""

    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    FILL_IN_THE_BLANK = "fill_in_the_blank"
    MATCHING = "matching"
    CODE = "code"


class MatchingPair(BaseModel):
    """One correct association of a matching question."""

    left: str
    right: str


class QuestionBase(BaseModel):
    quiz_id: str
    question_type: QuestionType = QuestionType.MULTIPLE_CHOICE
    text: str
    # Options-based types (multiple_choice, true_false): ``correct_option_id``
    # is the index (as a string) of the correct option inside ``options``, e.g. "0".
    options: List[str] = []
    correct_option_id: Optional[str] = None
    # Text-based types (short_answer, essay, fill_in_the_blank, code): the
    # expected answer text. ``acceptable_answers`` optionally lists alternates.
    correct_answer: Optional[str] = None
    acceptable_answers: List[str] = []
    matching_pairs: List[MatchingPair] = []  # matching questions only
    case_sensitive: bool = False  # applies to text-based grading

    @model_validator(mode="after")
    def _validate_type_required_fields(self):
        if self.question_type in (QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE):
            if self.correct_option_id is None:
                raise ValueError(
                    "multiple_choice / true_false questions require correct_option_id "
                    "(the index of the correct option as a string, e.g. \"0\")"
                )
        elif self.question_type in (
            QuestionType.SHORT_ANSWER,
            QuestionType.ESSAY,
            QuestionType.FILL_IN_THE_BLANK,
            QuestionType.CODE,
        ):
            if not (self.correct_answer or self.acceptable_answers):
                raise ValueError(
                    "this question type requires a correct_answer or acceptable_answers"
                )
        elif self.question_type == QuestionType.MATCHING:
            if not self.matching_pairs:
                raise ValueError(
                    "matching questions require at least one matching_pair (left/right)"
                )
        return self


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    quiz_id: Optional[str] = None
    question_type: Optional[QuestionType] = None
    text: Optional[str] = None
    options: Optional[List[str]] = None
    correct_option_id: Optional[str] = None
    correct_answer: Optional[str] = None
    acceptable_answers: Optional[List[str]] = None
    matching_pairs: Optional[List[MatchingPair]] = None
    case_sensitive: Optional[bool] = None


class Question(QuestionBase):
    id: Optional[PyObjectId] = None
    created_at: datetime = Field(default_factory=utcnow)


    model_config = ConfigDict(populate_by_name=True)