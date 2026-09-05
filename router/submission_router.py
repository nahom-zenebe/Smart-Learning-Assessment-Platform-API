from typing import List, Optional

from fastapi import APIRouter, HTTPException, status

from models.Submission import Submission, SubmissionCreate
from services.submission_service import SubmissionService

router = APIRouter(prefix="/submissions", tags=["Submissions"])
service = SubmissionService()


@router.post(
    "/", response_model=Submission, status_code=status.HTTP_201_CREATED
)
async def create_submission(submission: SubmissionCreate):
    """Submit quiz answers - the score is computed server-side."""
    return await service.create_submission(submission)


@router.get(
    "/", response_model=List[Submission], status_code=status.HTTP_200_OK
)
async def list_submissions(
    user_id: Optional[str] = None,
    quiz_id: Optional[str] = None,
    limit: int = 100,
):
    return await service.list_submissions(
        user_id=user_id, quiz_id=quiz_id, limit=limit
    )


@router.get(
    "/{submission_id}",
    response_model=Submission,
    status_code=status.HTTP_200_OK,
)
async def get_submission(submission_id: str):
    return await service.get_submission(submission_id)


@router.delete("/{submission_id}", status_code=status.HTTP_200_OK)
async def delete_submission(submission_id: str):
    await service.delete_submission(submission_id)
    return {"message": "Submission deleted successfully", "id": submission_id}
