from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.database import DBUser, DBAPIKey
from app.core.auth import get_current_user
from app.core.api_key import generate_api_key, hash_api_key
import datetime

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
async def register_user(email: str, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(DBUser).filter(DBUser.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = DBUser(email=email, plan="free")
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"status": "success", "user_id": new_user.id, "email": new_user.email}

@router.post("/api-key")
async def create_api_key(
    name: str, 
    user: DBUser = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required to create API keys")
        
    raw_key = generate_api_key()
    hashed_key = hash_api_key(raw_key)
    
    new_key = DBAPIKey(
        user_id=user.id,
        key_hash=hashed_key,
        name=name,
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(new_key)
    db.commit()
    return {"name": name, "api_key": raw_key}
