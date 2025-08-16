from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId

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

    
class Course(BaseModel):
    title:str=Field(...,min_length=5)
    description:optional[str]=None
    instructor_id: str
    category:str
    lessons: List[str] = []
    tags:[tags]
    created_at: datetime = datetime.utcnow()

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


