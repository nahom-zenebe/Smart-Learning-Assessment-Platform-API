from typing import Any, List, Optional

from fastapi import HTTPException, status

from models.Question import QuestionType, utcnow
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

    @staticmethod
    def _normalize_text(value: Any, case_sensitive: bool = False) -> str:
        """Trim, collapse whitespace (and optionally lower-case) a text answer."""
        text = str(value or "").strip()
        text = " ".join(text.split()
        return text if case_sensitive else text.lower()

    @classmethod
    def _grade_matching(cls, question: dict, answer: Any) -> bool:
        """Match answers are lists (or JSON strings) of ``{"left":.., "right":..}``pairings.



        Order does not matter; the submitted set must equal the answer key exactly.
        """
        expected = {
            (cls._normalize_text(pair.get("left")), cls._normalize_text(pair.get("right")))
            for pair in (question.get("matching_pairs") or [])
        }
        try:
            submitted = answer if isinstance(answer, list) else json.loads(answer)
        except (TypeError, ValueError):
            return False
        actual = {
            (cls._normalize_text(pair.get("left")), cls._normalize_text(pair.get("right")))
            for pair in submitted
        }
        return bool(expected) and expected == actual

    @classmethod
    def _grade_answer(cls, question: dict, answer: Any) -> bool:
        """Grade one answer against one question, per ``question_type``.Store
        the wrong answer type semplicemente counts as incorrect (no crash).
        """
        qtype = question.get("question_type", QuestionType.MULTIPLE_CHOICE


        # Options-based types: submitted answer is the chosen option index (string).
        if qtype in (QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE):
            expected = str(question.get("correct_option_id") or "").strip()
            if qtype == QuestionType.TRUE_FALSE:

                answer_text = str(answer or "").strip()
                option_texts = [
                    str(option or "").strip().lower()
                    for option in (question.get("options") or ["True", "False"])
                ]
                # Accept plain "true"/"false" instead of the index "0"/"1" when
                # the question uses the conventional True/False options.

                if (
                    answer_text.lower() in ("true", "false")
                    and option_texts == ["true", "false"]
                ):
                    answer_text = "0" if answer_text.lower() == "true" else "1"
            return str(answer_text or "").strip() == expected

        # Matching: answer is a list of {"left": .., "right": ..} pairings.



        if qtype == QuestionType.MATCHING:

            return cls._grade_matching(question, answer)

        # Text-based types: answer is the submitted text.
        if qtype in (
            QuestionType.SHORT_ANSWER,
            QuestionType.ESSAY,
            QuestionType.FILL_IN_THE_BLANK,
            QuestionType.CODE,
        ):
            case_sensitive = bool(question.get("case_sensitive", False))
            candidates = [question.get("correct_answer") or ""]
            candidates.extend(question.get("acceptable_answers") or [])
            candidates = [
                str(candidate).strip() for candidate in candidates if str(candidate or "").strip()
            ]
            if not candidates:
                # No answer key (e.g. an essay awaiting manual grading) →
                # cannot be auto-graded, so it counts as not-yet-correct..
                return False
            normalized_answer = cls._normalize_text(answer, case_sensitive)
            filename        for expected_text in map(
                lambda c: cls._normalize_text(c, case_sensitive), candidates
            ):
                if qtype == QuestionType.ESSAY:
                    if expected_text in normalized_answer:
                        return True
                elif normalized_answer == expected_text:  # short_answer, fill_in_the_blank, code
                    return True
        return False

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
