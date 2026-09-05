from typing import List, Optional, Tuple

from fastapi import HTTPException, status

from models.Progress import ProgressCreate, ProgressUpdate
from models.Question import utcnow
from repositories.progress_repository import ProgressRepository


class ProgressService:
    def __init__(self):
        self.repo = ProgressRepository()

    @staticmethod
    def _validate_counts(completed_lessons: int, total_lessons: int) -> None:
        if completed_lessons < 0 or total_lessons < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="completed_lessons and total_lessons must be >= 0",
            )
        if total_lessons > 0 and completed_lessons > total_lessons:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="completed_lessons cannot exceed total_lessons",
            )

    async def upsert_progress(self, data: ProgressCreate) -> Tuple[dict, bool]:
        """Create progress for a (user, course) pair or update the existing one.

        Returns ``(progress_doc, created)``.
        """
        self._validate_counts(data.completed_lessons, data.total_lessons)

        payload = data.model_dump()
        payload["last_updated"] = utcnow()

        existing = await self.repo.find_by_user_and_course(
            data.user_id, data.course_id
        )
        if existing:
            updated = await self.repo.update(existing["id"], payload)
            return updated, False

        progress_id = await self.repo.create(payload)
        return await self.repo.get_by_id(progress_id), True

    async def get_progress(self, progress_id: str) -> dict:
        progress = await self.repo.get_by_id(progress_id)
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Progress {progress_id} not found",
            )
        return progress

    async def list_progress(
        self,
        user_id: Optional[str] = None,
        course_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[dict]:
        return await self.repo.list_all(
            user_id=user_id, course_id=course_id, limit=limit
        )

    async def update_progress(
        self, progress_id: str, data: ProgressUpdate
    ) -> dict:
        existing = await self.get_progress(progress_id)
        update_data = data.model_dump(exclude_unset=True)

        completed = update_data.get(
            "completed_lessons", existing.get("completed_lessons", 0)
        )
        total = update_data.get(
            "total_lessons", existing.get("total_lessons", 0)
        )
        self._validate_counts(completed, total)

        update_data["last_updated"] = utcnow()
        updated = await self.repo.update(progress_id, update_data)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Progress {progress_id} not found",
            )
        return updated

    async def delete_progress(self, progress_id: str) -> None:
        if not await self.repo.delete(progress_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Progress {progress_id} not found",
            )
