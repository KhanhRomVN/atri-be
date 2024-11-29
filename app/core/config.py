from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Atri Chatbot API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    MYSQL_URL: str = os.getenv("MYSQL_URL")
    
    # Google API
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]

settings = Settings()