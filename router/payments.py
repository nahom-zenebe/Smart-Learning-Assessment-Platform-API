from fastapi import APIRouter, Depends
from app.services.stripe_service import StripeService



router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/create-intent")
def create_payment_intent(user_id: str, amount: int):
    client_secret = StripeService.create_payment_intent(user_id, amount)
    return {"client_secret": client_secret}