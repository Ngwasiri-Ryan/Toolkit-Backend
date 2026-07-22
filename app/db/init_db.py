from app.db.session import engine
from app.models.database import Base

def init_db() -> None:
    # Auto-create all tables mapped in Base schema
    Base.metadata.create_all(bind=engine)
