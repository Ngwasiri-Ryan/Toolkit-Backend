import pytest
import os
import shutil
import types
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app as fastapi_app
from app.db.session import get_db
from app.models.database import Base, DBUser, DBJob
from app.core.auth import get_current_user
from app.tasks.worker import task_remove_background
import app.services.mail

TEST_DATABASE_URL = "sqlite:///./test_toolkit_p7.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def mock_services(monkeypatch):
    monkeypatch.setattr(app.tasks.worker, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(app.routers.websocket, "SessionLocal", TestingSessionLocal)
    # Mock rembg
    fake_rembg = types.ModuleType("rembg")
    fake_rembg.remove = lambda data, *args, **kwargs: data
    monkeypatch.setitem(sys.modules, "rembg", fake_rembg)

    # Patch document conversion processes
    import app.services.document_service as doc_svc
    monkeypatch.setattr(doc_svc, "convert_md_to_pdf", lambda data: b"%PDF-mock")
    monkeypatch.setattr(doc_svc, "convert_docx_to_md", lambda data: b"# mock md")

    # Silence Redis pub/sub notifications
    import app.tasks.worker as worker_mod
    monkeypatch.setattr(worker_mod, "notify_job_update", lambda job_id, status: None)
    monkeypatch.setattr(worker_mod.task_remove_background, "delay", lambda *a, **kw: None)
    monkeypatch.setattr(worker_mod.task_convert_document, "delay", lambda *a, **kw: None)

    # Disable live Redis connection on websocket
    import redis.asyncio as aioredis
    monkeypatch.setattr(aioredis, "from_url", lambda *a, **k: ConnectionError("No Redis"))

    # Silence Resend emails
    monkeypatch.setattr(app.services.mail.settings, "RESEND_API_KEY", "")

@pytest.fixture(autouse=True)
def setup_db():
    if os.path.exists("test_toolkit_p7.db"):
        try: os.remove("test_toolkit_p7.db")
        except Exception: pass
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    user = DBUser(id="test_user_p7", email="p7_user@example.com", plan="free", daily_conversions_used=0)
    db.add(user)
    db.commit()
    db.close()
    
    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    fastapi_app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test_toolkit_p7.db"):
        try: os.remove("test_toolkit_p7.db")
        except Exception: pass
    if os.path.exists("local_storage"):
        shutil.rmtree("local_storage")

def override_get_db():
    db = TestingSessionLocal()
    try: yield db
    finally: db.close()

def override_get_current_user():
    db = TestingSessionLocal()
    user = db.query(DBUser).filter(DBUser.id == "test_user_p7").first()
    db.close()
    return user

client = TestClient(fastapi_app)

def test_full_platform_e2e_flow():
    # 1. Check Initial Free Quota
    usage_res = client.get("/api/v1/billing/usage")
    assert usage_res.status_code == 200
    assert usage_res.json()["plan"] == "free"
    assert usage_res.json()["daily_conversions_used"] == 0

    # 2. Convert 5 times (should deplete free limits)
    from PIL import Image
    import io
    img = Image.new("RGB", (10, 10), color="red")
    out = io.BytesIO()
    img.save(out, format="PNG")
    img_payload = out.getvalue()
    
    for i in range(5):
        conv_res = client.post(
            "/api/v1/images/compress",
            files={"file": (f"test_{i}.png", img_payload, "image/png")}
        )
        assert conv_res.status_code == 200

    # 3. 6th conversion attempt must fail with HTTP 429
    failed_conv = client.post(
        "/api/v1/images/compress",
        files={"file": ("test_failed.png", img_payload, "image/png")}
    )
    assert failed_conv.status_code == 429
    assert "limit" in failed_conv.json()["detail"]

    # 4. Initiate Upgrade Checkout Session
    checkout_res = client.post("/api/v1/billing/checkout")
    assert checkout_res.status_code == 200
    checkout_url = checkout_res.json()["checkout_url"]
    assert "mock-checkout" in checkout_url or "stripe" in checkout_url

    # 5. Simulate Stripe Checkout Upgrade Webhook Completed
    webhook_payload = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": "test_user_p7",
                "customer": "cus_e2e_p7",
                "customer_email": "p7_user@example.com"
            }
        }
    }
    webhook_res = client.post("/api/v1/billing/webhook", json=webhook_payload)
    assert webhook_res.status_code == 200

    # 6. Verify User Upgrade & Unlimited Usage
    usage_res = client.get("/api/v1/billing/usage")
    assert usage_res.json()["plan"] == "pro"
    assert usage_res.json()["daily_limit"] == -1

    # 7. Should now easily process 6th conversion with no quota limits
    success_conv = client.post(
        "/api/v1/images/compress",
        files={"file": ("test_unlimited.png", img_payload, "image/png")}
    )
    assert success_conv.status_code == 200
