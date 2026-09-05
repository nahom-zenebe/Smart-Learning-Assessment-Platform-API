from fastapi import APIRouter

from services.stripe_service import StripeService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/create-intent")
async def create_payment_intent(user_id: str, amount: float):
    """Create a Stripe PaymentIntent; ``amount`` is in dollars."""
    client_secret = await StripeService.create_payment_intent(user_id, amount)
    return {"client_secret": client_secret}
