from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.db import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    job_post_id = Column(Integer, ForeignKey("job_posts.id"), nullable=False, index=True)
    applicant_name = Column(String(255), nullable=False)
    applicant_email = Column(String(255), nullable=False, index=True)
    applicant_phone = Column(String(50), nullable=True)
    cv_document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    cover_letter_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    status = Column(String(50), nullable=False, default="pending", index=True) # pending, reviewed, shortlisted, rejected, accepted
    applied_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    hr_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    job_post = relationship("JobPost", backref="applications")
    cv_document = relationship("Document", foreign_keys=[cv_document_id])
    cover_letter_document = relationship("Document", foreign_keys=[cover_letter_document_id])

    # Constraints
    __table_args__ = (
        UniqueConstraint('job_post_id', 'applicant_email', name='uix_job_applicant_email'),
    )
    
    def __repr__(self):
        return f"<Application(id={self.id}, applicant='{self.applicant_email}', status='{self.status}')>"
