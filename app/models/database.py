from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
import uuid

Base = declarative_base()

class DBUser(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    plan = Column(String, default="free")  # free, pro, team
    stripe_customer_id = Column(String, nullable=True)
    daily_conversions_used = Column(Integer, default=0)
    last_reset_at = Column(DateTime, nullable=True)
    
    api_keys = relationship("DBAPIKey", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("DBJob", back_populates="user")

class DBJob(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    session_id = Column(String, nullable=True)  # For guest sessions
    tool = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed, expired
    input_path = Column(String, nullable=False)
    output_path = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    user = relationship("DBUser", back_populates="jobs")

class DBAPIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    key_hash = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    
    user = relationship("DBUser", back_populates="api_keys")
