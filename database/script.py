"""Deal with the Database connection."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Annotated
from fastapi import Depends
from config import get_settings

# Load settings
settings = get_settings()

# Setup engine based on environment
if get_settings().app_server == "deployment":
    engine = create_engine(
        get_settings().db_url,
        pool_size=3,        # Adjust pool size to suit your app
        max_overflow=0,     # Prevent DB overload on free-tier hosting
    )
else:
    
    # Local development with SQLite
    engine = create_engine(
        get_settings().db_url,
        connect_args={"check_same_thread": False},
    )

# Create DB session factory    
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base class for models
Base = declarative_base()

# Dependency to get a DB session per request
def get_db():
    """Provide a database session to the request, and close after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Annotated dependency (recommended in FastAPI 0.100+)
db_session = Annotated[Session, Depends(get_db)]