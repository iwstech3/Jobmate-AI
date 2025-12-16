from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.db import Base

class JobStatusHistory(Base):
    __tablename__ = "job_status_history"

    id = Column(Integer, primary_key=True, index=True)
    job_post_id = Column(Integer, ForeignKey("job_posts.id"), nullable=False, index=True)
    old_status = Column(String(50), nullable=False)
    new_status = Column(String(50), nullable=False)
    changed_reason = Column(Text, nullable=True)
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationship
    job_post = relationship("JobPost", backref="status_history")
    
    def __repr__(self):
        return f"<JobStatusHistory(job_id={self.job_post_id}, old={self.old_status}, new={self.new_status})>"
