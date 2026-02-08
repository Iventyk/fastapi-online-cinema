from pydantic import BaseModel


class StripeWebhookSchema(BaseModel):
    id: str
    type: str
    data: dict
