from core.security import create_access_token, hash_password, verify_password
from models.User import UserCreate, UserInDB
from repositories.user_repository import UserRepository


class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()

    async def register_user(self, user_data: UserCreate) -> UserInDB:
        if user_data.role.value == "admin":
            # Admins must be provisioned by an existing admin, never self-registered.
            raise ValueError("Admin accounts cannot be self-registered")

        existing = await self.user_repo.get_by_email(user_data.email)
        if existing:
            raise ValueError("User already exists")
        hashed_pw = hash_password(user_data.password)
        user_in_db = UserInDB(
            name=user_data.name,
            email=user_data.email,
            role=user_data.role,
            profile_picture=user_data.profile_picture,
            hashed_password=hashed_pw,
        )
        return await self.user_repo.create_user(user_in_db)

    async def login_user(self, email: str, password: str) -> str:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")
        token = create_access_token(
            {
                "sub": user.email,
                "user_id": str(user.id),
                "role": user.role.value,
            }
        )
        return token
