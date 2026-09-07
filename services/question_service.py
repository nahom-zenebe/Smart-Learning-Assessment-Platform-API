from typing import List

from fastapi import HTTPException, status

from models.Question import QuestionCreate, QuestionType, QuestionUpdate
from repositories.question_repository import QuestionRepository
from repositories.quiz_repository import QuizRepository


class QuestionService:
    def __init__(self):
        self.repo = QuestionRepository()
        self.quiz_repo = QuizRepository()

    @staticmethod
    def _validate_correct_option(options: List[str], correct_option_id: str) -> None:
        """correct_option_id is the index (as string) of the right option."""
        if not options:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A question must include at least one option",
            )
        try:
            index = int(correct_option_id)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="correct_option_id must be the index of the correct option "
                "as a string, e.g. '0'",
            )
        if index < 0 or index >= len(options):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"correct_option_id must be between 0 and {len(options) - 1}",
            )

    @staticmethod
    def _validate_question_fields(fields: dict) -> None:
        """Validate the type-specific fields of a (possibly merged) question.

        Runs on create and by the update path on the merged existing + new fields,
        so partial updates never leave a question in an invalid state.
        """
        qtype = fields.get("question_type", QuestionType.MULTIPLE_CHOICE)
        if qtype == QuestionType.TRUE_FALSE:
            options = fields.get("options") or ["True", "False"]
            QuestionService._validate_correct_option(
                options, fields.get("correct_option_id") or ""
            )
        elif qtype == QuestionType.MULTIPLE_CHOICE:
            QuestionService._validate_correct_option(
                fields.get("options") or [], fields.get("correct_option_id") or ""
            )
        elif qtype in (
            QuestionType.SHORT_ANSWER,
            QuestionType.ESSAY,
            QuestionType.FILL_IN_THE_BLANK,
            QuestionType.CODE,
        ):
            candidates = [fields.get("correct_answer") or ""]
            candidates.extend(fields.get("acceptable_answers") or [])
            if not any(str(candidate.strip()) for candidate in candidates):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"{qtype.value} questions require a correct_answer "
                        "or acceptable_answers"
                    ),
                )
        elif qtype == QuestionType.MATCHING:
            pairs = fields.get("matching_pairs") or []
            if not pairs:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="matching questions require at least one pair in matching_pairs",
                )
            for pair in pairs:
                if not str(pair.get("left") or "").strip() or not str(
                    pair.get("right") or ""
                ).strip():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="each matching pair needs non-empty 'left' and 'right' texts",
                    )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported question_type: {qtype}",
            )

    async def _quiz_or_404(self, quiz_id: str) -> dict:
        quiz = await self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz {quiz_id} not found",
            )
        return quiz

    async def create_question(self, data: QuestionCreate) -> dict:
        await self._quiz_or_404(data.quiz_id)
        payload = data.model_dump()
        if (
            data.question_type == QuestionType.TRUE_FALSE
            and not payload.get("options")
        ):
            payload["options"] = ["True", "False"]
        self._validate_question_fields(payload)

        question_id = await self.repo.create(payload)
        await self.quiz_repo.push_question(data.quiz_id, question_id)
        return await self.repo.get_by_id(question_id)

    async def get_question(self, question_id: str) -> dict:
        question = await self.repo.get_by_id(question_id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question {question_id} not found",
            )
        return question

    async def list_questions(self, limit: int = 100) -> List[dict]:
        return await self.repo.list_all(limit)

    async def list_questions_by_quiz(self, quiz_id: str) -> List[dict]:
        await self._quiz_or_404(quiz_id)
        return await self.repo.get_by_quiz(quiz_id)

    async def update_question(self, question_id: str, data: QuestionUpdate) -> dict:
        existing = await self.get_question(question_id)
        update_data = data.model_dump(exclude_unset=True)

        # Validate the merged (existing + changed) fields so partial updates
        # never leave a question in an invalid state for its question_type.
        merged = {**existing, **update_data}
        if (
            merged.get("question_type") == QuestionType.TRUE_FALSE
            and not merged.get("options")
        ):
            merged["options"] = ["True", "False"]
            update_data.setdefault("options", ["True", "False"])
        self._validate_question_fields(merged)

        old_quiz_id = existing["quiz_id"]
        new_quiz_id = update_data.get("quiz_id", old_quiz_id)
        if new_quiz_id != old_quiz_id:
            await self._quiz_or_404(new_quiz_id)

        updated = await self.repo.update(question_id, update_data)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question {question_id} not found",
            )

        # keep quiz <-> question links consistent
        if new_quiz_id != old_quiz_id:
            await self.quiz_repo.pull_question(old_quiz_id, question_id)
            await self.quiz_repo.push_question(new_quiz_id, question_id)
        return updated

    async def delete_question(self, question_id: str) -> None:
        existing = await self.get_question(question_id)
        if not await self.repo.delete(question_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question {question_id} not found",
            )
        await self.quiz_repo.pull_question(existing["quiz_id"], question_id)
