from typing import List, Optional

from fastapi import HTTPException, status

from models.Question import utcnow
from models.Submission import SubmissionCreate
from repositories.question_repository import QuestionRepository
from repositories.quiz_repository import QuizRepository
from repositories.submission_repository import SubmissionRepository
from services.notification_service import NotificationService

PASS_SCORE = 70.0


class SubmissionService:
    def __init__(self):
        self.repo = SubmissionRepository()
        self.quiz_repo = QuizRepository()
        self.question_repo = QuestionRepository()
        self.notifications = NotificationService()

    async def create_submission(self, data: SubmissionCreate) -> dict:
        """Grade a quiz attempt server-side and store the submission.

        Answers are positional: answers[i] is the chosen option index (as a
        string) for the i-th question of the quiz (ordered by creation).
        """
        quiz = await self.quiz_repo.get_by_id(data.quiz_id)
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz {data.quiz_id} not found",
            )

        questions = await self.question_repo.get_by_quiz(data.quiz_id)
        if not questions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Quiz '{quiz['title']}' has no questions yet",
            )
        if len(data.answers) != len(questions):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Expected {len(questions)} answers (one per question), "
                f"got {len(data.answers)}",
            )

        correct_count = sum(
            1
            for question, answer in zip(questions, data.answers)
            if str(answer).strip() == str(question.get("correct_option_id", "")).strip()
        )
        score = round(correct_count / len(questions) * 100, 2)

        payload = data.model_dump()
        payload["score"] = score
        payload["submitted_at"] = utcnow()

        submission_id = await self.repo.create(payload)
        submission = await self.repo.get_by_id(submission_id)

        # Best-effort grade notification (persisted + live WS push).
        try:
            await self.notifications.create_notification(
                user_id=payload["user_id"],
                title="Quiz graded",
                message=(
                    f"You scored {score}% on quiz '{quiz['title']}' "
                    f"({correct_count}/{len(questions)} correct)"
                ),
                notification_type="grade",
                data={
                    "submission_id": submission_id,
                    "quiz_id": data.quiz_id,
                    "score": score,
                    "passed": score >= PASS_SCORE,
                },
            )
        except Exception:
            pass  # notifications must never break the submission flow

        return submission

    async def get_submission(self, submission_id: str) -> dict:
        submission = await self.repo.get_by_id(submission_id)
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Submission {submission_id} not found",
            )
        return submission

    async def list_submissions(
        self,
        user_id: Optional[str] = None,
        quiz_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[dict]:
        return await self.repo.list_all(user_id=user_id, quiz_id=quiz_id, limit=limit)

    async def delete_submission(self, submission_id: str) -> None:
        if not await self.repo.delete(submission_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Submission {submission_id} not found",
            )
