from sqlalchemy import Column, Integer, String, DateTime, Boolean
from database import Base
import datetime

class ChatLog(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    user_message = Column(String(1000))
    bot_response = Column(String(1000))
    emotion = Column(String(50))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)