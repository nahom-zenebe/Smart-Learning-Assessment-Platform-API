from typing import List, Optional

from pydantic import BaseModel


class ScoreDistribution(BaseModel):
    bucket: str  # e.g. "0-49", "50-69", "70-89", "90-100"
    count: int = 0


class QuizAnalytics(BaseModel):
    quiz_id: str
    quiz_title: Optional[str] = None
    submissions: int = 0
    avg_score: float = 0.0
    min_score: float = 0.0
    max_score: float = 0.0
    pass_rate: float = 0.0  # % of submissions with score >= PASS_SCORE
    distribution: List[ScoreDistribution] = []


class QuestionAnalytics(BaseModel):
    question_id: str
    text: str = ""
    quiz_id: str = ""
    times_answered: int = 0
    times_correct: int = 0
    accuracy: float = 0.0  # % correct


class UserAnalytics(BaseModel):
    user_id: str
    submissions: int = 0
    quizzes_taken: int = 0
    avg_score: float = 0.0
    best_score: float = 0.0
    last_score: Optional[float] = None
    courses_in_progress: int = 0
    courses_completed: int = 0
    recent_submissions: List[dict] = []


class CourseAnalytics(BaseModel):
    course_id: str
    enrolled: int = 0
    avg_completion_pct: float = 0.0
    completed_count: int = 0
    in_progress_count: int = 0


class DashboardAnalytics(BaseModel):
    total_users: int = 0
    total_courses: int = 0
    total_quizzes: int = 0
    total_submissions: int = 0
    total_progress_records: int = 0
    overall_avg_score: float = 0.0
    overall_pass_rate: float = 0.0
    submissions_per_day: List[dict] = []
    top_quizzes: List[QuizAnalytics] = []