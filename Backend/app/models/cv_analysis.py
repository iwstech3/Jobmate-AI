"""
CV Analysis Database Model
Stores CV quality analysis results and improvement suggestions
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.db import Base


class CVAnalysis(Base):
    """CV Analysis results - quality scores and improvement suggestions"""
    __tablename__ = "cv_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    parsed_cv_id = Column(Integer, ForeignKey("parsed_cvs.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    # Scores (0-100)
    overall_score = Column(Integer, nullable=False, comment="Overall CV quality score")
    completeness_score = Column(Integer, nullable=False, comment="How complete the CV is")
    quality_score = Column(Integer, nullable=False, comment="Professional quality score")
    ats_score = Column(Integer, nullable=False, comment="ATS-friendliness score")
    
    # Analysis results (JSON arrays/objects)
    strengths = Column(JSON, nullable=False, comment="List of CV strengths")
    weaknesses = Column(JSON, nullable=False, comment="List of CV weaknesses")
    suggestions = Column(JSON, nullable=False, comment="Improvement suggestions with priority")
    skill_analysis = Column(JSON, nullable=False, comment="Detailed skill breakdown and gaps")
    experience_analysis = Column(JSON, nullable=False, comment="Career progression analysis")
    
    # Timestamps
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    parsed_cv = relationship("ParsedCV", back_populates="analysis")
    
    def __repr__(self):
        return f"<CVAnalysis(id={self.id}, parsed_cv_id={self.parsed_cv_id}, overall_score={self.overall_score})>"
