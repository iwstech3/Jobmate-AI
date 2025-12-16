from sqlalchemy import Column, Integer, String, Text, DateTime, func, Boolean
from app.database.db import Base

class JobPost(Base):
    __tablename__ = "job_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)  # Indexed for search
    company = Column(String(255), nullable=False, index=True)  # Indexed for search
    location = Column(String(255), nullable=True, index=True)  # Indexed for filtering
    job_type = Column(String(255), nullable=True, index=True)  # Indexed for filtering
    description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now()  # Auto-update on modification
    )
    
    # Analytics & Tracking
    views_count = Column(Integer, default=0, nullable=False)
    applications_count = Column(Integer, default=0, nullable=False)
    saves_count = Column(Integer, default=0, nullable=False)
    
    # Status & Visibility
    status = Column(String(50), default="published", nullable=False)  # draft, published, closed
    expires_at = Column(DateTime(timezone=True), nullable=True)
    featured = Column(Boolean, default=False)  # For premium/sponsored listings