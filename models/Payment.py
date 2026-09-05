from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from models.Question import utcnow


class Payment(BaseModel):
    id: Optional[str] = None
    user_id: str
    amount: float
    currency: str = "usd"
    status: str = "pending"
    stripe_payment_intent: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)

    