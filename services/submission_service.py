import json
from typing import Any

from models.Question import QuestionType


class SubmissionService:
    @staticmethod
    def _clean_text(value: Any, case_sensitive: bool = False) -> str:
        """Normalize a text answer: trim, collapse whitespace, optionally lowercase."""
        if value is None:
            text = ""
        else:
            text = str(value)

        text = text.strip()
        text = " ".join(text.split())

        if not case_sensitive:
            text = text.lower()

        return text

    @classmethod
    def _pair_key(cls, pair: dict) -> tuple:
        """Create a normalized key for a matching pair."""
        left = cls._clean_text(pair.get("left"))
        right = cls._clean_text(pair.get("right"))

        return (left, right)

    @classmethod
    def _grade_matching(cls, question: dict, answer: Any) -> bool:
        """Compare submitted matching pairs with the answer key.

        Order does not matter.
        """

    
        expected = set()

        pairs = question.get("matching_pairs") or []

        for pair in pairs:
            if isinstance(pair, dict):
                expected.add(cls._pair_key(pair))

    
        if isinstance(answer, list):
            submitted = answer
        else:
            try:
                loaded = answer or ""
                submitted = json.loads(loaded)
            except (TypeError, ValueError, json.JSONDecodeError):
                return False

        if not isinstance(submitted, list):
            return False

        
        actual = set()

        for pair in submitted:
            if isinstance(pair, dict):
                actual.add(cls._pair_key(pair))

     
        if not expected:
            return False

        return expected == actual

    @classmethod
    def _grade_answer(cls, question: dict, answer: Any) -> bool:
        """Grade one answer against one question."""

        qtype = question.get(
            "question_type",
            QuestionType.MULTIPLE_CHOICE,
        )

        # ---------------------------------------------------------
        # Multiple Choice / True-False
        # ---------------------------------------------------------
        if qtype in (
            QuestionType.MULTIPLE_CHOICE,
            QuestionType.TRUE_FALSE,
        ):
            expected = str(
                question.get("correct_option_id") or ""
            )

            answer_text = str(answer or "").strip()

            # True/False can accept:
            # "true" -> option 0
            # "false" -> option 1
            if qtype == QuestionType.TRUE_FALSE:
                options = question.get("options") or [
                    "True",
                    "False",
                ]

                option_texts = [
                    str(option or "").strip().lower()
                    for option in options
                ]

                if option_texts == ["true", "false"]:
                    lowered = answer_text.lower()

                    if lowered == "true":
                        answer_text = "0"
                    elif lowered == "false":
                        answer_text = "1"

            return answer_text == expected

        # ---------------------------------------------------------
        # Matching
        # ---------------------------------------------------------
        if qtype == QuestionType.MATCHING:
            return cls._grade_matching(question, answer)

        # ---------------------------------------------------------
        # Text-based questions
        # ---------------------------------------------------------
        if qtype in (
            QuestionType.SHORT_ANSWER,
            QuestionType.ESSAY,
            QuestionType.FILL_IN_THE_BLANK,
            QuestionType.CODE,
        ):
            case_sensitive = bool(
                question.get("case_sensitive", False)
            )

            candidates = []

            # Main correct answer
            correct_answer = question.get("correct_answer")

            if correct_answer is not None:
                if str(correct_answer).strip():
                    candidates.append(correct_answer)

            # Additional accepted answers
            accepted_answers = (
                question.get("acceptable_answers") or []
            )

            for item in accepted_answers:
                if item is not None and str(item).strip():
                    candidates.append(item)

            # No answer key available
            # For example, an essay may require manual grading.
            if not candidates:
                return False

            normalized_answer = cls._clean_text(
                answer,
                case_sensitive,
            )

            for candidate in candidates:
                normalized_candidate = cls._clean_text(
                    candidate,
                    case_sensitive,
                )

                # Essay:
                # Accept if the expected answer/key phrase
                # appears inside the submitted response.
                if qtype == QuestionType.ESSAY:
                    if normalized_candidate in normalized_answer:
                        return True

                # Other text questions:
                # Require exact normalized match.
                else:
                    if normalized_answer == normalized_candidate:
                        return True

            return False

        # Unknown question type
        return False
