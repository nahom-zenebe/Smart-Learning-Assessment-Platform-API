import stripe
from app.core.config import settings
from app.models.payment import Payment
from app.repositories.payment_repo import PaymentRepository


stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    @staticmethod
    def  create_payment_intent(user_id:str,amount:int,currency="usd"):
        intent=stripe.PaymentIntent.create(
            amount=amount,
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
        PaymentRepository.create(payment)
        return intent.client_secret