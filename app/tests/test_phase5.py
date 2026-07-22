import pytest
import os
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app as fastapi_app
from app.db.session import get_db
from app.models.database import Base, DBUser
from app.core.auth import get_current_user
from app.core.middleware import check_daily_quota
from fastapi import HTTPException

TEST_DATABASE_URL = "sqlite:///./test_toolkit_p5.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_db():
    if os.path.exists("test_toolkit_p5.db"):
        try: os.remove("test_toolkit_p5.db")
        except Exception: pass
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    user = DBUser(id="test_user_p5", email="p5_user@example.com", plan="free", daily_conversions_used=0)
    db.add(user)
    db.commit()
    db.close()
    
    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    fastapi_app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test_toolkit_p5.db"):
        try: os.remove("test_toolkit_p5.db")
        except Exception: pass

def override_get_db():
    db = TestingSessionLocal()
    try: yield db
    finally: db.close()

def override_get_current_user():
    db = TestingSessionLocal()
    user = db.query(DBUser).filter(DBUser.id == "test_user_p5").first()
    db.close()
    return user

client = TestClient(fastapi_app)

def test_usage_endpoint():
    response = client.get("/api/v1/billing/usage")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "p5_user@example.com"
    assert data["plan"] == "free"
    assert data["daily_limit"] == 5
    assert data["daily_conversions_used"] == 0
    assert data["conversions_remaining"] == 5
    assert data["is_quota_exceeded"] is False

def test_checkout_session():
    response = client.post("/api/v1/billing/checkout")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "checkout_url" in data

def test_stripe_webhook_upgrade_and_downgrade():
    # 1. Test checkout.session.completed (Upgrade to pro)
    payload_upgrade = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": "test_user_p5",
                "customer": "cus_stripe_mock_999",
                "customer_email": "p5_user@example.com"
            }
        }
    }
    response = client.post("/api/v1/billing/webhook", json=payload_upgrade)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Verify DB user updated to pro
    db = TestingSessionLocal()
    user = db.query(DBUser).filter(DBUser.id == "test_user_p5").first()
    assert user.plan == "pro"
    assert user.stripe_customer_id == "cus_stripe_mock_999"
    db.close()

    # 2. Test customer.subscription.deleted (Downgrade to free)
    payload_downgrade = {
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "customer": "cus_stripe_mock_999"
            }
        }
    }
    response = client.post("/api/v1/billing/webhook", json=payload_downgrade)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Verify DB user downgraded to free
    db = TestingSessionLocal()
    user = db.query(DBUser).filter(DBUser.id == "test_user_p5").first()
    assert user.plan == "free"
    db.close()

def test_daily_quota_middleware():
    db = TestingSessionLocal()
    user = db.query(DBUser).filter(DBUser.id == "test_user_p5").first()
    
    # Free user should succeed up to 5 conversions
    for i in range(5):
        user = check_daily_quota(user, db)
    assert user.daily_conversions_used == 5
    
    # 6th conversion attempt should raise HTTP 429
    with pytest.raises(HTTPException) as exc_info:
        check_daily_quota(user, db)
    assert exc_info.value.status_code == 429

    # Simulate 24-hour passage of time -> quota resets
    user.last_reset_at = datetime.now(timezone.utc) - timedelta(hours=25)
    db.commit()
    
    # Should succeed after reset
    user = check_daily_quota(user, db)
    assert user.daily_conversions_used == 1

    # Upgrade to pro -> unlimited conversions
    user.plan = "pro"
    user.daily_conversions_used = 100
    db.commit()
    user = check_daily_quota(user, db)
    assert user.daily_conversions_used == 101
    db.close()
