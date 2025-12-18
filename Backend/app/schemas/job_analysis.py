"""
Job Analysis Pydantic Schemas
Request/response models for job analysis API
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SalaryRange(BaseModel):
    """Salary range information"""
    min: Optional[int] = Field(None, description="Minimum salary")
    max: Optional[int] = Field(None, description="Maximum salary")
    currency: Optional[str] = Field(None, description="Currency code (e.g., USD, EUR)")
    period: Optional[str] = Field(None, description="Payment period: annual, monthly, hourly")
    
    class Config:
        from_attributes = True


class JobAnalysisBase(BaseModel):
    """Base Job Analysis schema"""
    required_skills: List[str] = Field(default_factory=list, description="Must-have technical skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Nice-to-have skills")
    experience_level: str = Field(..., description="Experience level: entry, junior, mid, senior, lead, principal")
    min_years_experience: Optional[int] = Field(None, description="Minimum years of experience")
    max_years_experience: Optional[int] = Field(None, description="Maximum years of experience")
    education_requirements: List[str] = Field(default_factory=list, description="Education requirements")
    certifications: List[str] = Field(default_factory=list, description="Certifications mentioned")
    responsibilities: List[str] = Field(default_factory=list, description="Key responsibilities")
    benefits: List[str] = Field(default_factory=list, description="Benefits and perks")
    salary_range: Optional[SalaryRange] = Field(None, description="Salary range information")
    employment_type: str = Field(..., description="Employment type: full-time, part-time, contract, internship")
    remote_policy: Optional[str] = Field(None, description="Remote policy: on-site, hybrid, fully-remote, flexible")
    industry: Optional[str] = Field(None, description="Industry sector")
    company_size: Optional[str] = Field(None, description="Company size: startup, small, medium, large, enterprise")
    key_technologies: List[str] = Field(default_factory=list, description="Top technologies mentioned")
    soft_skills: List[str] = Field(default_factory=list, description="Soft skills required")


class JobAnalysisCreate(JobAnalysisBase):
    """Schema for creating job analysis in database"""
    job_post_id: int


class JobAnalysisOut(JobAnalysisBase):
    """Schema for job analysis API response"""
    id: int
    job_post_id: int
    analyzed_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
