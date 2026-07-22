import secrets
import hashlib
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.database import DBAPIKey, DBUser

API_KEY_PREFIX = "tk_live_"

def generate_api_key() -> str:
    # Generates a random secure token with standard prefix
    raw_token = secrets.token_hex(20)
    return f"{API_KEY_PREFIX}{raw_token}"

def hash_api_key(api_key: str) -> str:
    # Return SHA-256 hash of API key for storage matching
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()

async def validate_api_key(
    x_api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> DBUser:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API Key missing")
        
    hashed_key = hash_api_key(x_api_key)
    key_entry = db.query(DBAPIKey).filter(DBAPIKey.key_hash == hashed_key).first()
    
    if not key_entry:
        raise HTTPException(status_code=401, detail="API Key invalid")
        
    user = db.query(DBUser).filter(DBUser.id == key_entry.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="API Key owner user not found")
        
    return user
