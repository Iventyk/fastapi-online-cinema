import stripe
from fastapi import APIRouter, Request, HTTPException

from src.config import get_settings

webhooks_router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
settings = get_settings()


@webhooks_router.post("/stripe")
async def stripe_webhook(request: Request) -> dict[str, str]:
    payload = await request.body()
    signature = request.headers.get("Stripe-Signature")

    try:
        stripe.Webhook.construct_event( # type: ignore[no-untyped-call]
            payload=payload,
            sig_header=signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return {"status": "ok"}
