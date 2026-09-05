from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from core.security import get_current_user
from models.Submission import Submission, SubmissionCreate
from services.submission_service import SubmissionService

router = APIRouter(prefix="/submissions", tags=["Submissions"])
service = SubmissionService()


@router.post(
    "/", response_model=Submission, status_code=status.HTTP_201_CREATED
)
async def create_submission(
    submission: SubmissionCreate,
    user: dict = Depends(get_current_user),
):
    """Submit quiz answers - the score is computed server-side.

    A non-admin user may only submit under their own account.
    """
    owner = str(user.get("id"))
    if submission.user_id != owner and user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Submissions can only be created for your own account",
        )
    return await service.create_submission(submission)


@router.get(
    "/", response_model=List[Submission], status_code=status.HTTP_200_OK
)
async def list_submissions(
    user_id: Optional[str] = None,
    quiz_id: Optional[str] = None,
    limit: int = 100,
    user: dict = Depends(get_current_user),
):
    # Non-admins only ever see their own submissions.
    if user.get("role") != "admin":
        user_id = str(user.get("id"))
    return await service.list_submissions(
        user_id=user_id, quiz_id=quiz_id, limit=limit
    )


@router.get(
    "/{submission_id}",
    response_model=Submission,
    status_code=status.HTTP_200_OK,
)
async def get_submission(
    submission_id: str,
    user: dict = Depends(get_current_user),
):
    submission = await service.get_submission(submission_id)
    # Non-admins can only read their own submissions.
    if (
        user.get("role") != "admin"
        and str(submission.get("user_id")) != str(user.get("id"))
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view another user's submission",
        )
    return submission


@router.delete("/{submission_id}", status_code=status.HTTP_200_OK)
async def delete_submission(submission_id: str):
    await service.delete_submission(submission_id)
    return {"message": "Submission deleted successfully", "id": submission_id}
