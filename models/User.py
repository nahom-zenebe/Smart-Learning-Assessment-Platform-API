from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from models.objectid import PyObjectId


class UserRole(str, Enum):
    admin = "admin"
    student = "student"
    instructor = "instructor"


class UserBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    role: UserRole = UserRole.student
    profile_picture: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserInDB(UserBase):
    id: Optional[PyObjectId] = None
    hashed_password: str

    model_config = ConfigDict(populate_by_name=True)


class UserResponse(UserBase):
    id: Optional[str] = None

