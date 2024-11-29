from sqlalchemy import Column, Integer, String, DateTime, Boolean
from app.db.base import Base
import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ChatLog(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    user_message = Column(String(1000))
    bot_response = Column(String(1000))
    emotion = Column(String(500))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)