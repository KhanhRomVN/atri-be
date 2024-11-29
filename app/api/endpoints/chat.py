from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.schemas.chat import ChatInput, ChatResponse, ChatLog
from app.services.chat import ChatService
from typing import List
import csv
from datetime import datetime
import os

router = APIRouter()

@router.post("/english/chat", response_model=ChatResponse)
async def chat(chat_input: ChatInput, db: Session = Depends(get_db)):
    chat_service = ChatService(db)
    return await chat_service.process_chat(chat_input)

@router.post("/vietnamese/chat", response_model=ChatResponse)
async def chat_vietnamese(chat_input: ChatInput, db: Session = Depends(get_db)):
    chat_service = ChatService(db)
    return await chat_service.process_vietnamese_chat(chat_input)

@router.get("/chat-history", response_model=List[ChatLog])
async def get_chat_history(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    logs = db.query(ChatLog).offset(skip).limit(limit).all()
    return logs

@router.get("/export-logs")
async def export_logs(db: Session = Depends(get_db)):
    try:
        logs = db.query(ChatLog).all()
        
        if not os.path.exists('data'):
            os.makedirs('data')
            
        filename = f"data/chat_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ID', 'User Message', 'Bot Response', 'Emotion', 'Timestamp'])
            
            for log in logs:
                writer.writerow([
                    log.id,
                    log.user_message,
                    log.bot_response,
                    log.emotion,
                    log.timestamp
                ])
        
        return {"message": f"Logs exported successfully to {filename}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))