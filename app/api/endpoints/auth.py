from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.schemas.user import UserCreate, Token
from app.services.auth import AuthService

router = APIRouter()

@router.post("/register", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.register_user(user)

@router.post("/login", response_model=Token)
async def login(user: UserCreate, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.authenticate_user(user.email, user.password)