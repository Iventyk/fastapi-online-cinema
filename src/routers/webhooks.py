from fastapi import APIRouter, Request, HTTPException, Depends

import stripe
from src.config import get_settings
from src.services.payment import handle_stripe_webhook
from sqlalchemy.ext.asyncio import AsyncSession
from src.databases import get_db
from src.notifications.emails import EmailSender

webhooks_router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
settings = get_settings()


@webhooks_router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    email_service: EmailSender = Depends(),
) -> dict[str, str]:
    """
    Receive Stripe webhook and update Payment and Order status.
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

    await handle_stripe_webhook(
        db=db, event=event, email_service=email_service
    )
    return {"status": "ok"}
