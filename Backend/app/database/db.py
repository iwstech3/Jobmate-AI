from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Render specifics: force SSL and avoid fork issues
connect_args = {}
if DATABASE_URL and ("render.com" in DATABASE_URL or "internal" in DATABASE_URL):
    # Force use of SSL
    if "sslmode=" not in DATABASE_URL:
        separator = "&" if "?" in DATABASE_URL else "?"
        DATABASE_URL += f"{separator}sslmode=require"
    connect_args["sslmode"] = "require"

# Using NullPool on Render is the safest way to avoid the "decryption failed" SSL error
# which occurs when connections are shared between worker processes.
from sqlalchemy.pool import NullPool

engine = create_engine(
    DATABASE_URL,
    echo=True,  # Log SQL for easier debugging
    poolclass=NullPool if (DATABASE_URL and "render.com" in DATABASE_URL) else None,
    connect_args=connect_args
)
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