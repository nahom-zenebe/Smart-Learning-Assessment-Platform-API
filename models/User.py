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
    created_at: datetime = datetime.utcnow()
