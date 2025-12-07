"""
CV Analysis Pydantic Schemas
Request/response models for CV analysis API
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Suggestion(BaseModel):
    """Individual improvement suggestion"""
    category: str = Field(..., description="Category: skills, experience, format, content, contact_info, achievements")
    priority: str = Field(..., description="Priority: high, medium, low")
    suggestion: str = Field(..., description="Specific actionable advice")
    
    class Config:
        from_attributes = True


class SkillAnalysis(BaseModel):
    """Detailed skill breakdown"""
    technical_skills: List[str] = Field(default_factory=list, description="Technical/hard skills identified")
    soft_skills: List[str] = Field(default_factory=list, description="Soft skills identified")
    skill_level: str = Field(..., description="Overall skill level: beginner, intermediate, advanced, expert")
    missing_common_skills: List[str] = Field(default_factory=list, description="Common skills missing for the field")
    
    class Config:
        from_attributes = True


class ExperienceAnalysis(BaseModel):
    """Career progression analysis"""
    total_years: Optional[int] = Field(None, description="Total years of experience")
    career_progression: str = Field(..., description="Progression: positive, lateral, unclear")
    recent_experience: str = Field(..., description="Relevance: relevant, somewhat_relevant, not_relevant")
    job_stability: str = Field(..., description="Stability: excellent, good, concerning")
    
    class Config:
        from_attributes = True


class CVAnalysisBase(BaseModel):
    """Base CV Analysis schema"""
    overall_score: int = Field(..., ge=0, le=100, description="Overall CV quality score (0-100)")
    completeness_score: int = Field(..., ge=0, le=100, description="Completeness score (0-100)")
    quality_score: int = Field(..., ge=0, le=100, description="Professional quality score (0-100)")
    ats_score: int = Field(..., ge=0, le=100, description="ATS-friendliness score (0-100)")
    strengths: List[str] = Field(..., description="List of CV strengths")
    weaknesses: List[str] = Field(..., description="List of CV weaknesses")
    suggestions: List[Suggestion] = Field(..., description="Improvement suggestions")
    skill_analysis: SkillAnalysis = Field(..., description="Detailed skill analysis")
    experience_analysis: ExperienceAnalysis = Field(..., description="Career progression analysis")


class CVAnalysisCreate(CVAnalysisBase):
    """Schema for creating CV analysis in database"""
    parsed_cv_id: int


class CVAnalysisOut(CVAnalysisBase):
    """Schema for CV analysis API response"""
    id: int
    parsed_cv_id: int
    analyzed_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
