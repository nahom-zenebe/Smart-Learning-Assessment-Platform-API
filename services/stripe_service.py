import stripe

from config import STRIPE_SECRET_KEY
from models.Payment import Payment
from repositories.payment_repo import PaymentRepository

stripe.api_key = STRIPE_SECRET_KEY


class StripeService:
    @staticmethod
    async def create_payment_intent(
        user_id: str, amount: float, currency: str = "usd"
    ) -> str:
        """Create a Stripe PaymentIntent; ``amount`` is in dollars."""
        intent = stripe.PaymentIntent.create(
            amount=int(round(amount * 100)),
            currency=currency,
            metadata={"user_id": user_id},
            automatic_payment_methods={"enabled": True},
        )
        payment = Payment(
            user_id=user_id,
            amount=amount,
            currency=currency,
            status="pending",
            stripe_payment_intent=intent.id,
        )
        await PaymentRepository().create(payment.model_dump(exclude={"id"}))
        return intent.client_secret
