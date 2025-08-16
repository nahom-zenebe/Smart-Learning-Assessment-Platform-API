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

class Question(BaseModel):
    id:Optional[str]
    quiz_id:str
    text:str
    options:List[str]=[]
    correct_option_id:str