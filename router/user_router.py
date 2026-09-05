from fastapi import APIRouter, HTTPException, Response, status

from models.User import UserCreate, UserResponse
from services.user_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])
auth_service = AuthService()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(user: UserCreate):
    try:
        created_user = await auth_service.register_user(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return UserResponse(
        id=created_user.id,
        name=created_user.name,
        email=created_user.email,
        role=created_user.role,
        profile_picture=created_user.profile_picture,
    )


@router.post("/login")
async def login(user: UserCreate, response: Response):
    try:
        token = await auth_service.login_user(user.email, user.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    response.set_cookie(key="access_token", value=token, httponly=True)
    return {"access_token": token, "token_type": "bearer"}

