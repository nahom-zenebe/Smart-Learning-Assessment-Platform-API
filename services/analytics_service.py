from typing import List

from fastapi import HTTPException, status

from repositories.analytics_repository import AnalyticsRepository
from repositories.course_repository import CourseRepository
from repositories.question_repository import QuestionRepository
from repositories.quiz_repository import QuizRepository


class AnalyticsService:
    def __init__(self):
        self.repo = AnalyticsRepository()
        self.quiz_repo = QuizRepository()
        self.question_repo = QuestionRepository()
        self.course_repo = CourseRepository()

    # --- dashboard -------------------------------------------------------

    async def dashboard(self) -> dict:
        users = self.repo.users
        courses = self.repo.courses
        quizzes = self.repo.quizzes
        progress = self.repo.progress
        submissions = self.repo.submissions

        overall = await self.repo.overall_score_summary()

        return {
            "total_users": await self.repo.count_documents(users),
            "total_courses": await self.repo.count_documents(courses),
            "total_quizzes": await self.repo.count_documents(quizzes),
            "total_submissions": await self.repo.count_documents(submissions),
            "total_progress_records": await self.repo.count_documents(progress),
            "overall_avg_score": overall["avg_score"],
            "overall_pass_rate": overall["pass_rate"],
            "submissions_per_day": await self.repo.submissions_per_day(days=30),
            "top_quizzes": await self.all_quizzes_analytics(limit=5),
        }

    # --- quizzes ---------------------------------------------------------

    async def all_quizzes_analytics(self, limit: int = 50) -> List[dict]:
        summaries = await self.repo.all_quiz_score_summaries(limit=limit)
        quizzes = await self.quiz_repo.list_all(limit=100000)
        titles = {q["id"]: q["title"] for q in quizzes}

        result = []
        for row in summaries:
            result.append(
                {
                    "quiz_id": row["quiz_id"],
                    "quiz_title": titles.get(row["quiz_id"]),
                    "submissions": row["submissions"],
                    "avg_score": row["avg_score"],
                    "min_score": row["min_score"],
                    "max_score": row["max_score"],
                    "pass_rate": row["pass_rate"],
                    "distribution": [],
                }
            )
        return result

    async def quiz_analytics(self, quiz_id: str) -> dict:
        quiz = await self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz {quiz_id} not found",
            )
        summary = await self.repo.quiz_score_summary(quiz_id)
        distribution = await self.repo.score_distribution({"quiz_id": quiz_id})

        return {
            "quiz_id": quiz_id,
            "quiz_title": quiz.get("title"),
            "submissions": summary["total"],
            "avg_score": summary["avg_score"],
            "min_score": summary["min_score"],
            "max_score": summary["max_score"],
            "pass_rate": summary["pass_rate"],
            "distribution": distribution,
# --- questions --------------------------------------------------------

    async def question_analytics(self, question_id: str) -> dict:
        question = await self.question_repo.get_by_id(question_id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question {question_id} not found",
            )

        quiz_questions = await self.question_repo.get_by_quiz(question["quiz_id"])
        index = next(
            (i for i, q in enumerate(quiz_questions) if q["id"] == question_id),
            None,
        )
        if index is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question is not linked to any quiz",
            )

        rows = await self.repo.submission_rows({"quiz_id": question["quiz_id"]})
        times_answered = 0
        times_correct = 0
        for submission in rows:
            answers = submission.get("answers") or []
            if index >= len(answers):
                continue
            times_answered += 1
            if (
                str(answers[index]).strip()
                == str(question.get("correct_option_id", "")).strip()
            ):
                times_correct += 1

        return {
            "question_id": question_id,
            "text": question.get("text", ""),
            "quiz_id": question.get("quiz_id", ""),
            "times_answered": times_answered,
            "times_correct": times_correct,
            "accuracy": round(times_correct / times_answered * 100, 2)
            if times_answered
            else 0.0,
        }

    # --- users -----------------------------------------------------------

    async def user_analytics(self, user_id: str) -> dict:
        submissions = await self.repo.submission_rows({"user_id": user_id})
        progress_rows = await self.repo.progress_rows({"user_id": user_id})

        scores = [s.get("score") or 0 for s in submissions]
        quizzes_taken = len({s.get("quiz_id") for s in submissions})

        completed = sum(
            1
            for p in progress_rows
            if p.get("total_lessons")
            and (p.get("completed_lessons") or 0) >= p.get("total_lessons", 0)
        )
        in_progress = len(progress_rows) - completed

        recent = [
            {
                "id": str(s.get("_id")),
                "quiz_id": s.get("quiz_id"),
                "score": s.get("score"),
                "submitted_at": s.get("submitted_at"),
            }
            for s in submissions[:5]
        ]

        return {
            "user_id": user_id,
            "submissions": len(submissions),
            "quizzes_taken": quizzes_taken,
            "avg_score": round(sum(scores) / len(scores), 2) if scores else 0.0,
            "best_score": max(scores) if scores else 0.0,
            "last_score": scores[0] if scores else None,  # newest first
            "courses_in_progress": in_progress,
            "courses_completed": completed,
            "recent_submissions": recent,
        }

    # --- courses ---------------------------------------------------------

    async def course_analytics(self, course_id: str) -> dict:
        course = await self.course_repo.get_by_id(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course {course_id} not found",
            )

        rows = await self.repo.progress_rows({"course_id": course_id})
        percentages = []
        completed = 0
        for p in rows:
            total = p.get("total_lessons") or 0
            done = p.get("completed_lessons") or 0
            if total > 0:
                percentages.append(min(done / total * 100, 100.0))
                if done >= total:
                    completed += 1

        return {
            "course_id": course_id,
            "enrolled": len(rows),
            "avg_completion_pct": round(
                sum(percentages) / len(percentages), 2
            )
            if percentages
            else 0.0,
            "completed_count": completed,
            "in_progress_count": len(rows) - completed,
        }
        }