from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy.orm import Session
from app.models.database import DBUser
from app.core.config import settings

def setup_middlewares(app: FastAPI):
    """
    Configures global middlewares including CORS and GZip response compression.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

def check_daily_quota(user: DBUser, db: Session) -> DBUser:
    """
    Verifies and enforces the daily conversion quota for free-tier users.
    Resets daily counter if more than 24 hours have passed since last_reset_at.
    Raises HTTP 429 if the daily limit is exceeded.
    Increments daily_conversions_used if permitted.
    """
    user = db.merge(user)
    now = datetime.now(timezone.utc)
    
    # Calculate timezone-aware timestamp difference
    last_reset = user.last_reset_at
    if last_reset:
        if last_reset.tzinfo is None:
            last_reset = last_reset.replace(tzinfo=timezone.utc)
        time_diff = (now - last_reset).total_seconds()
    else:
        time_diff = 86400  # Force reset if no previous timestamp

    if time_diff >= 86400:
        user.daily_conversions_used = 0
        user.last_reset_at = now
        db.commit()
        db.refresh(user)

    if user.plan == "free":
        if user.daily_conversions_used >= settings.FREE_DAILY_CONVERSION_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily conversion limit of {settings.FREE_DAILY_CONVERSION_LIMIT} reached. Upgrade to Pro for unlimited usage."
            )

    user.daily_conversions_used += 1
    db.commit()
    db.refresh(user)
    return user
