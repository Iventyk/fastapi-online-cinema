from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import stripe

from src.config import get_settings
from src.services.stripe_webhook import handle_stripe_webhook
from src.databases import get_db

webhooks_router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
settings = get_settings()


@webhooks_router.post(
    "/stripe",
    summary="Stripe Webhook",
    description="Receive Stripe webhook and update Payment and Order status.",
)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Receive Stripe webhook and update Payment and Order status.
    Emails are sent asynchronously via Celery tasks.
    """
    payload = await request.body()
    signature = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    await handle_stripe_webhook(db=db, event=event)

    return {"status": "ok"}
