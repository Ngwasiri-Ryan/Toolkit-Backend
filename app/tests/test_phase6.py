import pytest
import os
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app as fastapi_app
from app.db.session import get_db
from app.models.database import Base, DBUser, DBJob
from app.core.auth import get_current_user
from app.core.security import validate_safe_filename, validate_file_size, sanitize_svg_content
from app.services.mail import send_completion_email
import app.services.mail

TEST_DATABASE_URL = "sqlite:///./test_toolkit_p6.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_db():
    if os.path.exists("test_toolkit_p6.db"):
        try: os.remove("test_toolkit_p6.db")
        except Exception: pass
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    user = DBUser(id="test_user_p6", email="p6_user@example.com", plan="free")
    db.add(user)
    db.commit()
    db.close()
    
    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    fastapi_app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test_toolkit_p6.db"):
        try: os.remove("test_toolkit_p6.db")
        except Exception: pass

def override_get_db():
    db = TestingSessionLocal()
    try: yield db
    finally: db.close()

def override_get_current_user():
    db = TestingSessionLocal()
    user = db.query(DBUser).filter(DBUser.id == "test_user_p6").first()
    db.close()
    return user

client = TestClient(fastapi_app)

def test_path_traversal_detection():
    # Direct function checks
    with pytest.raises(HTTPException) as exc_info:
        validate_safe_filename("../etc/passwd")
    assert exc_info.value.status_code == 400

    with pytest.raises(HTTPException) as exc_info:
        validate_safe_filename("image/../../test.png")
    assert exc_info.value.status_code == 400

    # API Endpoint checks
    response = client.post(
        "/api/v1/images/grayscale", 
        files={"file": ("../../malicious.png", b"fake_png_data", "image/png")}
    )
    assert response.status_code == 400
    assert "traversal" in response.json()["detail"]

def test_file_size_limiter():
    # Test directly
    # 51MB of data should fail (limit is 50MB)
    huge_data = b"0" * (51 * 1024 * 1024)
    with pytest.raises(HTTPException) as exc_info:
        validate_file_size(huge_data)
    assert exc_info.value.status_code == 413

    # Small data should pass
    validate_file_size(b"small")

def test_svg_sanitization(monkeypatch):
    # Embedded script inside SVG tag
    svg_input = b'<svg><script>alert("XSS")</script><rect onload="javascript:alert(1)" width="100"/></svg>'
    sanitized = sanitize_svg_content(svg_input)
    
    # Assert tag and attributes removed
    assert b"script" not in sanitized
    assert b"onload" not in sanitized
    assert b"alert" not in sanitized

    # Validate API filters SVG upload
    svg_upload = b'<svg><script>alert("XSS")</script></svg>'
    import app.services.image_service as img_svc
    monkeypatch.setattr(img_svc, "compress_image", lambda content, *a, **kw: content)

    response = client.post(
        "/api/v1/images/compress",
        files={"file": ("test.svg", svg_upload, "image/svg+xml")}
    )
    assert response.status_code == 200

def test_email_dispatch_flow(monkeypatch):
    # Mock HTTP call for Resend API call
    dispatched = []
    
    def mock_post(url, json, headers, timeout):
        dispatched.append(json)
        class MockResponse:
            status_code = 200
            text = "success"
        return MockResponse()

    # Monkeypatch settings to simulate active Resend API key
    monkeypatch.setattr(app.services.mail.settings, "RESEND_API_KEY", "re_mock_key_123")
    monkeypatch.setattr(app.services.mail.settings, "RESEND_FROM_EMAIL", "test@toolkit.dev")
    monkeypatch.setattr(app.services.mail.httpx, "post", mock_post)

    success = send_completion_email("user@example.com", "job_uuid_123", "http://download.url")
    assert success is True
    assert len(dispatched) == 1
    assert dispatched[0]["to"] == ["user@example.com"]
    assert "job_uuid_123" in dispatched[0]["subject"]
