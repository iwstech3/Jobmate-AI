from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

class SkillMatch(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0, description="Skill match score (0.0-1.0)")
    matched_required: List[str] = Field(default_factory=list)
    missing_required: List[str] = Field(default_factory=list)
    matched_preferred: List[str] = Field(default_factory=list)
    missing_preferred: List[str] = Field(default_factory=list)
    additional_skills: List[str] = Field(default_factory=list)
    match_rate: float = Field(..., description="Percentage of required skills matched")
    critical_missing: List[str] = Field(default_factory=list, description="Missing skills identified as critical")

class ExperienceMatch(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0, description="Experience match score (0.0-1.0)")
    candidate_years: int
    required_years: int
    gap: int
    assessment: Literal["exceeds", "meets_requirement", "slightly_below", "significantly_below"]
    details: str

class EducationMatch(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0, description="Education match score (0.0-1.0)")
    candidate_education: List[str] = Field(default_factory=list)
    required_education: List[str] = Field(default_factory=list)
    meets_requirement: bool

class WorkExperienceRelevance(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0.0-1.0)")
    relevant_positions: int
    total_positions: int
    recent_experience_relevant: bool
    career_progression: str

class SemanticSimilarity(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0, description="Semantic similarity score (0.0-1.0)")
    interpretation: str

class Recommendation(BaseModel):
    type: Literal["for_candidate", "for_hr"]
    priority: Literal["high", "medium", "low"]
    recommendation: str

class CompatibilityScore(BaseModel):
    overall_score: int = Field(..., ge=0, le=100, description="Overall compatibility score (0-100)")
    match_percentage: int = Field(..., ge=0, le=100)
    recommendation: Literal["highly_recommended", "recommended", "potential_fit", "not_recommended"]
    
    skill_match: SkillMatch
    experience_match: ExperienceMatch
    education_match: EducationMatch
    work_experience_relevance: WorkExperienceRelevance
    semantic_similarity: SemanticSimilarity
    
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommendations: List[Recommendation] = Field(default_factory=list)
    interview_focus_areas: List[str] = Field(default_factory=list)

class CompatibilityRequest(BaseModel):
    parsed_cv_id: int
    job_post_id: int

class BatchCompatibilityRequest(BaseModel):
    parsed_cv_id: int
    job_post_ids: List[int]
