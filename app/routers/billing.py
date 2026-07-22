from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.auth import get_current_user
from app.models.database import DBUser
from app.core.config import settings
import stripe
import json

router = APIRouter(prefix="/billing", tags=["billing"])

if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY

@router.get("/usage")
def get_usage_metrics(current_user: DBUser = Depends(get_current_user)):
    """
    Returns user plan metadata, current daily conversion counts, and remaining quota.
    Used by frontend to trigger ad placements or display upgrade prompts.
    """
    limit = settings.FREE_DAILY_CONVERSION_LIMIT if current_user.plan == "free" else -1
    used = current_user.daily_conversions_used or 0
    remaining = max(0, limit - used) if limit != -1 else 999999
    
    return {
        "user_id": str(current_user.id),
        "email": current_user.email,
        "plan": current_user.plan,
        "daily_conversions_used": used,
        "daily_limit": limit,
        "conversions_remaining": remaining,
        "is_quota_exceeded": current_user.plan == "free" and used >= limit
    }

@router.post("/checkout")
def create_checkout_session(current_user: DBUser = Depends(get_current_user)):
    """
    Generates a Stripe Checkout session URL for upgrading to Pro.
    Falls back to mock simulation URL if Stripe key is unconfigured.
    """
    if not settings.STRIPE_SECRET_KEY:
        return {
            "status": "success",
            "checkout_url": f"https://billing.toolkit.dev/mock-checkout?user_id={current_user.id}"
        }
        
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": settings.PRO_PRICE_ID,
                "quantity": 1,
            }],
            mode="subscription",
            customer_email=current_user.email,
            client_reference_id=str(current_user.id),
            success_url="https://toolkit.dev/billing/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://toolkit.dev/billing/cancel",
        )
        return {"status": "success", "checkout_url": session.url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe session creation failed: {str(e)}"
        )

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handles Stripe webhooks (checkout.session.completed, customer.subscription.deleted).
    Updates user plan status in database accordingly.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    event = None
    if settings.STRIPE_WEBHOOK_SECRET and sig_header:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Webhook signature error: {str(e)}")
    else:
        try:
            event = json.loads(payload.decode("utf-8"))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid webhook JSON payload")
            
    event_type = event.get("type")
    data_object = event.get("data", {}).get("object", {})
    
    if event_type in ("checkout.session.completed", "customer.subscription.created"):
        user_id = data_object.get("client_reference_id")
        customer_email = data_object.get("customer_email") or data_object.get("email")
        
        user = None
        if user_id:
            user = db.query(DBUser).filter(DBUser.id == user_id).first()
        elif customer_email:
            user = db.query(DBUser).filter(DBUser.email == customer_email).first()
            
        if user:
            user.plan = "pro"
            user.stripe_customer_id = data_object.get("customer")
            db.commit()
            return {"status": "success", "message": f"User {user.email} upgraded to pro"}

    elif event_type == "customer.subscription.deleted":
        customer_id = data_object.get("customer")
        if customer_id:
            user = db.query(DBUser).filter(DBUser.stripe_customer_id == customer_id).first()
            if user:
                user.plan = "free"
                db.commit()
                return {"status": "success", "message": f"User {user.email} downgraded to free"}

    return {"status": "ignored", "event_type": event_type}
