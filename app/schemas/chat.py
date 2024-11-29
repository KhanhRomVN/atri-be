from pydantic import BaseModel
from typing import List, Tuple, Optional
from datetime import datetime

class ChatInput(BaseModel):
    message: str
    conversation_history: List[Tuple[str, str]] = []

class ChatResponse(BaseModel):
    response: str
    emotion: str

class ChatLog(BaseModel):
    id: int
    user_message: str
    bot_response: str
    emotion: str
    timestamp: datetime

    class Config:
        from_attributes = True