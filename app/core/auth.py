from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.models.database import DBUser

security = HTTPBearer(auto_error=False)

def verify_token(token: str) -> dict:
    try:
        # Decodes the payload based on the configured secret
        payload = jwt.decode(token, settings.SUPABASE_JWT_SECRET, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> DBUser | None:
    if not credentials:
        return None  # Enable guest access
    
    payload = verify_token(credentials.credentials)
    user_email = payload.get("email")
    if not user_email:
        raise HTTPException(status_code=401, detail="Token payload invalid")
        
    user = db.query(DBUser).filter(DBUser.email == user_email).first()
    return user
