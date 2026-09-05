from typing import List, Optional, Tuple

from fastapi import HTTPException, status

from models.Progress import ProgressCreate, ProgressUpdate
from models.Question import utcnow
from repositories.progress_repository import ProgressRepository
from services.notification_service import NotificationService


class ProgressService:
    def __init__(self):
        self.repo = ProgressRepository()
        self.notifications = NotificationService()

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
            await self._notify_progress(updated, created=False)
            return updated, False

        progress_id = await self.repo.create(payload)
        progress = await self.repo.get_by_id(progress_id)
        await self._notify_progress(progress, created=True)
        return progress, True

    async def _notify_progress(self, progress: Optional[dict], created: bool) -> None:
        """Best-effort progress/completion notification (never fails the flow)."""
        if not progress:
            return
        completed = progress.get("completed_lessons") or 0
        total = progress.get("total_lessons") or 0
        course_id = progress.get("course_id", "")
        if total > 0 and completed >= total:
            title, ntype = "Course completed 🎉", "success"
            message = f"You finished all {total} lessons of course {course_id}!"
        else:
            title, ntype = "Progress updated", "progress"
            action = "started" if created else "updated"
            message = (
                f"Progress {action} for course {course_id}: "
                f"{completed}/{total} lessons completed"
            )
        try:
            await self.notifications.create_notification(
                user_id=str(progress.get("user_id")),
                title=title,
                message=message,
                notification_type=ntype,
                data={
                    "progress_id": progress.get("id"),
                    "course_id": course_id,
                    "completed_lessons": completed,
                    "total_lessons": total,
                },
            )
        except Exception:
            pass

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
