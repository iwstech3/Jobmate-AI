from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.db import Base

class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_post_id = Column(Integer, ForeignKey("job_posts.id"), nullable=False, index=True)
    user_email = Column(String(255), nullable=False, index=True)
    notes = Column(Text, nullable=True)
    
    saved_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    job_post = relationship("JobPost", backref="saved_by")

    # Constraints
    __table_args__ = (
        UniqueConstraint('job_post_id', 'user_email', name='uix_saved_job_user'),
    )
    
    def __repr__(self):
        return f"<SavedJob(id={self.id}, user='{self.user_email}', job_id={self.job_post_id})>"
