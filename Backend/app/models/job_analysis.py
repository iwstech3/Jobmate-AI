"""
Job Analysis Database Model
Stores structured data extracted from job descriptions
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.db import Base


class JobAnalysis(Base):
    """Job Analysis results - structured requirements and metadata"""
    __tablename__ = "job_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    job_post_id = Column(Integer, ForeignKey("job_posts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    # Skills
    required_skills = Column(JSON, nullable=False, default=list, comment="Must-have technical skills")
    preferred_skills = Column(JSON, nullable=False, default=list, comment="Nice-to-have skills")
    
    # Experience
    experience_level = Column(String(50), nullable=False, comment="entry/junior/mid/senior/lead/principal")
    min_years_experience = Column(Integer, nullable=True, comment="Minimum years of experience")
    max_years_experience = Column(Integer, nullable=True, comment="Maximum years of experience")
    
    # Requirements
    education_requirements = Column(JSON, nullable=False, default=list, comment="Education requirements")
    certifications = Column(JSON, nullable=False, default=list, comment="Certifications mentioned")
    
    # Job details
    responsibilities = Column(JSON, nullable=False, default=list, comment="Key responsibilities")
    benefits = Column(JSON, nullable=False, default=list, comment="Benefits and perks")
    
    # Compensation
    salary_range = Column(JSON, nullable=True, comment="Salary range object with min, max, currency, period")
    
    # Employment details
    employment_type = Column(String(50), nullable=False, comment="full-time/part-time/contract/internship")
    remote_policy = Column(String(50), nullable=True, comment="on-site/hybrid/fully-remote/flexible")
    
    # Company & industry
    industry = Column(String(100), nullable=True, comment="Industry sector")
    company_size = Column(String(50), nullable=True, comment="startup/small/medium/large/enterprise")
    
    # Technology & skills
    key_technologies = Column(JSON, nullable=False, default=list, comment="Top technologies mentioned")
    soft_skills = Column(JSON, nullable=False, default=list, comment="Soft skills required")
    
    # Timestamps
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    job_post = relationship("JobPost", back_populates="analysis")
    
    def __repr__(self):
        return f"<JobAnalysis(id={self.id}, job_post_id={self.job_post_id}, experience_level='{self.experience_level}')>"
