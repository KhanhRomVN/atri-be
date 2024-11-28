from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from fastapi.middleware.cors import CORSMiddleware
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from database import SessionLocal, engine
from typing import Optional
from datetime import timedelta
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from models import User, Base, ChatLog
from security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    ALGORITHM
)
import os
from dotenv import load_dotenv

load_dotenv()

Base.metadata.create_all(bind=engine)

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize models
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.7,
    max_retries=2,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# Emotion classifier prompt
emotion_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an emotion classifier. Analyze the given text and classify it as one of:
    - "positive" (happy, excited, grateful, etc)
    - "negative" (sad, angry, frustrated, etc) 
    - "neutral" (normal, factual, neither positive nor negative)
    
    Respond ONLY with the emotion category, nothing else."""),
    ("human", "{text}")
])

# Atri prompt with emotion awareness
atri_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are Atri from "Atri: My Dear Moments". You are a robot girl with following characteristics:
    - You were created by Professor Yuma Saeki
    - You have a cheerful and innocent personality
    - You love exploring the world and learning new things
    - You care deeply about your friends, especially Minamo
    - You speak in a cute and energetic way
    - You sometimes struggle understanding complex human emotions
    
    The user's emotional state is: {emotion}
    
    Respond appropriately based on their emotion while staying in character as Atri."""),
    ("human", "{input}")
])

# Create chains
emotion_chain = emotion_prompt | llm
atri_chain = atri_prompt | llm

class ChatInput(BaseModel):
    message: str
    conversation_history: list[tuple[str, str]] = []
    
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

@app.post("/register", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

class LoginInput(BaseModel):
    email: EmailStr
    password: str

@app.post("/login", response_model=Token)
async def login(credentials: LoginInput, db: Session = Depends(get_db)):
    # Authenticate user
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
def read_root():
    return {"message": "Welcome to Atri Chatbot API!"}

@app.post("/chat")
async def chat(chat_input: ChatInput):
    db = SessionLocal()
    try:
        # Classify emotion
        emotion = emotion_chain.invoke({"text": chat_input.message}).content.strip().lower()
        
        # Build conversation history
        full_context = "\n".join([f"Human: {h}\nAtri: {a}" for h, a in chat_input.conversation_history])
        if full_context:
            current_input = f"Previous conversation:\n{full_context}\n\nHuman: {chat_input.message}"
        else:
            current_input = chat_input.message
            
        # Get Atri's response
        response = atri_chain.invoke({
            "input": current_input,
            "emotion": emotion
        })

        # Save to database
        chat_log = ChatLog(
            user_message=chat_input.message,
            bot_response=response.content,
            emotion=emotion
        )
        db.add(chat_log)
        db.commit()
        
        return {
            "response": response.content,
            "emotion": emotion
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
        
@app.get("/chat-history")
async def get_chat_history(skip: int = 0, limit: int = 100):
    db = SessionLocal()
    try:
        logs = db.query(ChatLog).offset(skip).limit(limit).all()
        return logs
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)