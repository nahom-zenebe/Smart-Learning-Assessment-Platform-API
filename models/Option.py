from typing import Optional

from pydantic import BaseModel, ConfigDict

from models.objectid import PyObjectId


class OptionBase(BaseModel):
    question_id: str
    text: str


class OptionCreate(OptionBase):
    pass


class Option(OptionBase):
    id: Optional[PyObjectId] = None

    model_config = ConfigDict(populate_by_name=True)



    