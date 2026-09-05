from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status

from core.security import get_current_user
from models.Progress import Progress, ProgressCreate, ProgressUpdate
from services.progress_service import ProgressService

router = APIRouter(prefix="/progress", tags=["Progress"])
service = ProgressService()


@router.post("/", response_model=Progress, status_code=status.HTTP_201_CREATED)
async def upsert_progress(
    progress: ProgressCreate,
    response: Response,
    user: dict = Depends(get_current_user),
):
    """Create progress for a (user, course) pair, or update it if it exists
    (returns 200 instead of 201 when updating). Non-admins can only update
    their own progress."""
    owner = str(user.get("id"))
    if progress.user_id != owner and user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Progress can only be updated for your own account",
        )
    doc, created = await service.upsert_progress(progress)
    if not created:
        response.status_code = status.HTTP_200_OK
    return doc


@router.get(
    "/", response_model=List[Progress], status_code=status.HTTP_200_OK
)
async def list_progress(
    user_id: Optional[str] = None,
    course_id: Optional[str] = None,
    limit: int = 100,
    user: dict = Depends(get_current_user),
):
    # Non-admins only ever see their own progress.
    if user.get("role") != "admin":
        user_id = str(user.get("id"))
    return await service.list_progress(
        user_id=user_id, course_id=course_id, limit=limit
    )


@router.get(
    "/{progress_id}", response_model=Progress, status_code=status.HTTP_200_OK
)
async def get_progress(
    progress_id: str,
    user: dict = Depends(get_current_user),
):
    progress = await service.get_progress(progress_id)
    # Non-admins can only read their own progress.
    if (
        user.get("role") != "admin"
        and str(progress.get("user_id")) != str(user.get("id"))
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view another user's progress",
        )
    return progress


@router.put(
    "/{progress_id}", response_model=Progress, status_code=status.HTTP_200_OK
)
async def update_progress(
    progress_id: str,
    progress: ProgressUpdate,
    user: dict = Depends(get_current_user),
):
    existing = await service.get_progress(progress_id)
    if (
        user.get("role") != "admin"
        and str(existing.get("user_id")) != str(user.get("id"))
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update another user's progress",
        )
    return await service.update_progress(progress_id, progress)


@router.delete("/{progress_id}", status_code=status.HTTP_200_OK)
async def delete_progress(progress_id: str):
    await service.delete_progress(progress_id)
    return {"message": "Progress deleted successfully", "id": progress_id}
