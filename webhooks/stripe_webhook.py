import stripe
from fastapi import APIRouter,Request,HTTPException
from app.core.config import settings
from app.repositories.payment_repo import PaymentRepository



router = APIRouter(prefix="/webhook", tags=["Stripe Webhook"])


@router.post("/stripe")
async def stripe_webhook(request:Request):
    payload=aeait request.body()
    sig_header=request.headers.get("stripe_signature")
    try:
        event=stripe.webhook.construct_event(
            payload,sig_header,settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(status_code=400,detail=str(e))
    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        PaymentRepository.update_status(intent["id"], "succeeded")

    elif event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        PaymentRepository.update_status(intent["id"], "failed")

    return {"status": "success"}