from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId
from enum import Enum




class UserRole(str,Enum):
    admin="admin",
    student = "student"
    instructor = "instructor"
    
#help for vaildaite the serialization
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators_(cls):
        yield cls.validate
   @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class User(BaseModel):
    name:str=Field(...,min_lenght=3,max_length=30)
    email:EmailStr
    password_hash:str
    role:UserRole
    profile_picture:str
    

class UserInDB(BaseModel):
    id:Optional[str]=None
    name:str
    email:EmailStr
    hash_password:str
    role:UserRole
    profile_picture:str

class UserResponse(BaseModel):
    name:str
    email:EmailStr
    role:UserRole
    profile_picture:str


    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
