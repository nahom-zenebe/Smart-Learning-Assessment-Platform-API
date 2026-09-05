import stripe
from fastapi import APIRouter, HTTPException, Request

from config import STRIPE_WEBHOOK_SECRET
from repositories.payment_repo import PaymentRepository

router = APIRouter(prefix="/webhooks", tags=["Stripe Webhook"])


@router.post("/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        await PaymentRepository().update_status(intent["id"], "succeeded")

    elif event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        await PaymentRepository().update_status(intent["id"], "failed")

    return {"status": "success"}
