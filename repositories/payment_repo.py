from typing import Optional

from db.mongodb import get_database, serialize_doc


class PaymentRepository:
    COLLECTION = "payments"

    @property
    def collection(self):
        return get_database()[self.COLLECTION]

    async def create(self, data: dict) -> str:
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def update_status(self, payment_intent_id: str, status: str) -> bool:
        result = await self.collection.update_one(
            {"stripe_payment_intent": payment_intent_id},
            {"$set": {"status": status}},
        )
        return result.modified_count > 0

    async def get_by_intent(self, intent_id: str) -> Optional[dict]:
        doc = await self.collection.find_one(
            {"stripe_payment_intent": intent_id}
        )
        return serialize_doc(doc)

