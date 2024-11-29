from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Convert MySQL URL to SQLAlchemy format
db_url = settings.MYSQL_URL.replace("mysql://", "mysql+pymysql://")
db_url = db_url.replace("?ssl-mode=REQUIRED", "")

engine = create_engine(
    db_url,
    connect_args={"ssl": {"ssl_mode": "REQUIRED"}}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()