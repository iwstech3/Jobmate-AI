from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Add this function - it was missing!
def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session to route handlers.
    Automatically closes the session after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()