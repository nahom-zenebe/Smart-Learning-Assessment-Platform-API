from fastapi import APIRouter, HTTPException, Response, Depends
from app.models.User import UserCreate, UserResponse
from app.services.user_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate):
    try:
        created_user = auth_service.register_user(user)
        return UserResponse(email=created_user.email, full_name=created_user.full_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
def login(user: UserCreate, response: Response):
    try:
        token = auth_service.login_user(user.email, user.password)
        response.set_cookie(key="access_token", value=token, httponly=True)
        return {"access_token": token, "token_type": "bearer"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
