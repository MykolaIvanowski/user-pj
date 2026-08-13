from sqlalchemy import Column, Integer, String, JSON, Boolean
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(1024), nullable=True)
    metadata = Column(JSON, nullable=True)

    is_deleted = Column(Boolean, default=False)
