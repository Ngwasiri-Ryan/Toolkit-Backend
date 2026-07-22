import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import get_db
from app.models.database import Base, DBUser, DBAPIKey
from app.core.api_key import hash_api_key

# Scoped testing database setup
TEST_DATABASE_URL = "sqlite:///./test_toolkit.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def run_around_tests():
    # Setup test schema
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    # Teardown test schema
    Base.metadata.drop_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

client = TestClient(app)

def test_user_registration():
    response = client.post("/api/v1/auth/register?email=newuser@example.com")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["email"] == "newuser@example.com"
    
    # Try duplicate registration
    duplicate = client.post("/api/v1/auth/register?email=newuser@example.com")
    assert duplicate.status_code == 400

def test_api_key_header_authorization():
    # Register user
    client.post("/api/v1/auth/register?email=dev@example.com")
    
    # Inject user mock validation and query API key generation
    db = TestingSessionLocal()
    user = db.query(DBUser).filter(DBUser.email == "dev@example.com").first()
    
    # Mocking standard Supabase token extraction return info
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user
    
    response = client.post("/api/v1/auth/api-key?name=testkey")
    assert response.status_code == 200
    res_data = response.json()
    raw_api_key = res_data["api_key"]
    assert raw_api_key.startswith("tk_live_")
    
    # Clean override maps
    app.dependency_overrides.pop(get_current_user, None)
