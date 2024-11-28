from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# Convert MySQL URL to SQLAlchemy format with proper SSL config
db_url = os.getenv("MYSQL_URL").replace("mysql://", "mysql+pymysql://")
db_url = db_url.replace("?ssl-mode=REQUIRED", "")  # Remove the ssl-mode parameter

# Create engine with SSL configuration
engine = create_engine(
    db_url,
    connect_args={
        "ssl": {
            "ssl_mode": "REQUIRED"
        }
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()