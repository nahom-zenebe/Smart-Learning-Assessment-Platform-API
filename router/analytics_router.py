from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from core.security import get_current_user
from models.Analytics import (
    CourseAnalytics,
    DashboardAnalytics,
    QuestionAnalytics,
    QuizAnalytics,
    UserAnalytics,
)
from services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])
service = AnalyticsService()


@router.get(
    "/dashboard",
    response_model=DashboardAnalytics,
    status_code=status.HTTP_200_OK,
)
async def dashboard(_: dict = Depends(get_current_user)):
    """Platform-wide overview (admin only - enforced by RoleAccessMiddleware)."""
    return await service.dashboard()


@router.get(
    "/quizzes",
    response_model=List[QuizAnalytics],
    status_code=status.HTTP_200_OK,
)
async def all_quiz_analytics(
    limit: int = 50, _: dict = Depends(get_current_user)
):
    return await service.all_quizzes_analytics(limit=min(limit, 200))


@router.get(
    "/quizzes/{quiz_id}",
    response_model=QuizAnalytics,
    status_code=status.HTTP_200_OK,
)
async def quiz_analytics(quiz_id: str, _: dict = Depends(get_current_user)):
    return await service.quiz_analytics(quiz_id)


@router.get(
    "/questions/{question_id}",
    response_model=QuestionAnalytics,
    status_code=status.HTTP_200_OK,
)
async def question_analytics(
    question_id: str, _: dict = Depends(get_current_user)
):
    return await service.question_analytics(question_id)


@router.get(
    "/users/{user_id}",
    response_model=UserAnalytics,
    status_code=status.HTTP_200_OK,
)
async def user_analytics(
    user_id: str, user: dict = Depends(get_current_user)
):
    # Any authenticated user can view their own analytics; only admins can
    # view someone else's.
    if user.get("role") != "admin" and str(user.get("id")) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view another user's analytics",
        )
    return await service.user_analytics(user_id)


@router.get(
    "/courses/{course_id}",
    response_model=CourseAnalytics,
    status_code=status.HTTP_200_OK,
)
async def course_analytics(
    course_id: str, _: dict = Depends(get_current_user)
):
    return await service.course_analytics(course_id)