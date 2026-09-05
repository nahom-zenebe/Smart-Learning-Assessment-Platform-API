from typing import List, Optional

from fastapi import APIRouter, HTTPException, Response, status

from models.Progress import Progress, ProgressCreate, ProgressUpdate
from services.progress_service import ProgressService

router = APIRouter(prefix="/progress", tags=["Progress"])
service = ProgressService()


@router.post("/", response_model=Progress, status_code=status.HTTP_201_CREATED)
async def upsert_progress(progress: ProgressCreate, response: Response):
    """Create progress for a (user, course) pair, or update it if it exists
    (returns 200 instead of 201 when updating)."""
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
):
    return await service.list_progress(
        user_id=user_id, course_id=course_id, limit=limit
    )


@router.get(
    "/{progress_id}", response_model=Progress, status_code=status.HTTP_200_OK
)
async def get_progress(progress_id: str):
    return await service.get_progress(progress_id)


@router.put(
    "/{progress_id}", response_model=Progress, status_code=status.HTTP_200_OK
)
async def update_progress(progress_id: str, progress: ProgressUpdate):
    return await service.update_progress(progress_id, progress)


@router.delete("/{progress_id}", status_code=status.HTTP_200_OK)
async def delete_progress(progress_id: str):
    await service.delete_progress(progress_id)
    return {"message": "Progress deleted successfully", "id": progress_id}
