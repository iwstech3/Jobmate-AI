from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.db import Base

class JobView(Base):
    __tablename__ = "job_views"

    id = Column(Integer, primary_key=True, index=True)
    job_post_id = Column(Integer, ForeignKey("job_posts.id"), nullable=False, index=True)
    viewer_email = Column(String(255), nullable=True)  # Nullable for anonymous users
    viewer_ip = Column(String(50), nullable=True)      # For anonymous tracking
    user_agent = Column(String(500), nullable=True)
    referrer = Column(String(500), nullable=True)
    viewed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationship
    job_post = relationship("JobPost", backref="views")
