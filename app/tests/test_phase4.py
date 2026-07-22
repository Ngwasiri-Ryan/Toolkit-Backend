import pytest
import os
import shutil
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app as fastapi_app
from app.db.session import get_db
from app.models.database import Base, DBJob, DBUser
import app.tasks.worker
from app.tasks.worker import task_remove_background, task_convert_document
from app.core.auth import get_current_user

TEST_DATABASE_URL = "sqlite:///./test_toolkit_p4.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

import app.routers.websocket
app.tasks.worker.SessionLocal = TestingSessionLocal
app.routers.websocket.SessionLocal = TestingSessionLocal

@pytest.fixture(autouse=True)
def mock_services(monkeypatch):
    import sys
    import types

    # Inject a fake rembg module BEFORE worker.py imports it
    # This prevents the heavy AI model download on first import
    fake_rembg = types.ModuleType("rembg")
    fake_rembg.remove = lambda data, *args, **kwargs: data
    monkeypatch.setitem(sys.modules, "rembg", fake_rembg)

    # Patch document_service functions directly — avoids pypandoc/reportlab execution
    import app.services.document_service as doc_svc
    monkeypatch.setattr(doc_svc, "convert_md_to_pdf", lambda data: b"%PDF-mock")
    monkeypatch.setattr(doc_svc, "convert_docx_to_md", lambda data: b"# mock md")

    # Silence Redis pub/sub notifications in worker — no Redis running in tests
    import app.tasks.worker as worker_mod
    monkeypatch.setattr(worker_mod, "notify_job_update", lambda job_id, status: None)

    # Prevent Celery .delay() from trying to connect to Redis broker
    # Tests call the task functions directly instead
    import app.tasks.worker as wm
    monkeypatch.setattr(wm.task_remove_background, "delay", lambda *a, **kw: None)
    monkeypatch.setattr(wm.task_convert_document, "delay", lambda *a, **kw: None)

    # Instantly trigger DB polling fallback in WebSocket router during tests
    import redis.asyncio as aioredis
    def mock_redis_from_url(*a, **kw):
        raise ConnectionError("No Redis in test environment")
    monkeypatch.setattr(aioredis, "from_url", mock_redis_from_url)

@pytest.fixture(autouse=True)
def setup_db():
    if os.path.exists("test_toolkit_p4.db"):
        try: os.remove("test_toolkit_p4.db")
        except Exception: pass
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    user = db.query(DBUser).filter(DBUser.email == "test@example.com").first()
    if not user:
        user = DBUser(id="test_user_1", email="test@example.com", plan="free")
        db.add(user)
        db.commit()
    db.close()
    
    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    fastapi_app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("local_storage"):
        shutil.rmtree("local_storage")

def override_get_db():
    db = TestingSessionLocal()
    try: yield db
    finally: db.close()

def override_get_current_user():
    db = TestingSessionLocal()
    user = db.query(DBUser).filter(DBUser.id == "test_user_1").first()
    db.close()
    return user

client = TestClient(fastapi_app)

def test_background_removal_flow():
    img_data = b"fake_png_data"
    response = client.post("/api/v1/images/remove-background", files={"file": ("test.png", img_data, "image/png")})
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    task_remove_background(job_id)
    
    poll_response = client.get(f"/api/v1/jobs/{job_id}")
    assert poll_response.status_code == 200
    assert poll_response.json()["status"] == "completed"
    
    dl_response = client.get(f"/api/v1/jobs/{job_id}/download")
    assert dl_response.status_code == 200
    assert dl_response.headers["content-type"] == "image/png"

def test_document_conversion_flow():
    md_data = b"# Hello World"
    response = client.post("/api/v1/documents/convert/md-to-pdf", files={"file": ("test.md", md_data, "text/markdown")})
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    task_convert_document(job_id, "pdf")
    
    poll_response = client.get(f"/api/v1/jobs/{job_id}")
    assert poll_response.status_code == 200
    assert poll_response.json()["status"] == "completed"
    
    dl_response = client.get(f"/api/v1/jobs/{job_id}/download")
    assert dl_response.status_code == 200
    assert dl_response.content.startswith(b"%PDF")

def test_job_websocket_flow():
    db = TestingSessionLocal()
    job = DBJob(id="ws_job", user_id="test_user_1", tool="md-to-pdf", status="completed", input_path="dummy")
    db.add(job)
    db.commit()
    db.close()
    with client.websocket_connect("/ws/jobs/ws_job") as websocket:
        msg = websocket.receive_json()
        assert msg["job_id"] == "ws_job"
        assert msg["status"] == "completed"
