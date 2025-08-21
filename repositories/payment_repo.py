from app.db.mongodb import db
from app.models.payment import Payment


class PaymentRepository:
    def __init__(self):
        self.collection=df["payments"]

    def create(self,payment:Payment):
        result=self.collection.insert_one(payment)
        return str(result.inserted_id) 

    def update_status(self, payment_intent_id: str, status: str):
        self.collection.update_one(
            {"stripe_payment_intent": payment_intent_id},
            {"$set": {"status": status}}
        )
        
    def get_by_intent(self, intent_id: str):
        return self.collection.find_one({"stripe_payment_intent": intent_id})
