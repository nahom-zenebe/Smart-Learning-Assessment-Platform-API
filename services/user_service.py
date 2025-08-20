from app.repositories.user_repository import UserRepository
from app.models.User import UserCreate, UserInDB
from app.core.security import hash_password, verify_password, create_access_token

class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()

    def register_user(self, user_data: UserCreate):
        existing = self.user_repo.get_by_email(user_data.email)
        if existing:
            raise ValueError("User already exists")
        hashed_pw = hash_password(user_data.password)
        user_in_db = UserInDB(email=user_data.email, full_name=user_data.full_name, hashed_password=hashed_pw)
        return self.user_repo.create_user(user_in_db)

    def login_user(self, email: str, password: str):
        user = self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")
        token = create_access_token({"sub": user.email})
        return token
