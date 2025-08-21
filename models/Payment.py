from pydantic import BaseModel,Field
from datetime import datetime
from bson import ObjectId


class Payment(BaseModel):
    id:str=Field(default=None,alias="_id")
    user_id:str
    amount:str
    currency:str="usd"
    status:str="pending"
    stripe_payment_intent:str|None=None
    created_at:datetime=datetime.utcnow()

    