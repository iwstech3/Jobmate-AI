from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.db import Base

class CoverLetter(Base):
    __tablename__ = "cover_letters"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_posts.id"), nullable=False)
    parsed_cv_id = Column(Integer, ForeignKey("parsed_cvs.id"), nullable=False)
    content = Column(Text, nullable=False)
    customization_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("JobPost", backref="cover_letters")
    parsed_cv = relationship("ParsedCV", backref="cover_letters")
