from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.database.db import Base

class ParsedCV(Base):
    """
    Model for storing structured data extracted from CVs/Resumes.
    """
    __tablename__ = "parsed_cvs"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, unique=True)
    
    # Personal Info
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    
    # Structured Data (stored as JSON)
    skills = Column(JSON, nullable=True)
    experience_years = Column(Integer, nullable=True)
    education = Column(JSON, nullable=True)
    work_experience = Column(JSON, nullable=True)
    certifications = Column(JSON, nullable=True)
    
    # Summary
    summary = Column(Text, nullable=True)
    
    # Raw extracted text for reference or re-parsing
    raw_text = Column(Text, nullable=True)
    
    # Timestamps
    parsed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    document = relationship("Document", backref="parsed_cv")

    def __repr__(self):
        return f"<ParsedCV(id={self.id}, name='{self.name}', document_id={self.document_id})>"
