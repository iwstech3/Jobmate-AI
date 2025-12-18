from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class JobMatchResult(BaseModel):
    """
    Schema for a single job match result when searching for jobs for a candidate.
    """
    job_id: int
    job_title: str
    company: str
    location: Optional[str] = None
    similarity_score: float = Field(..., description="0-1 Semantic similarity score", ge=0.0, le=1.0)
    skill_match_score: float = Field(..., description="0-1 Skill overlap score", ge=0.0, le=1.0)
    experience_match_score: float = Field(..., description="0-1 Experience level match score", ge=0.0, le=1.0)
    overall_match_score: float = Field(..., description="Weighted average of all scores", ge=0.0, le=1.0)
    match_percentage: int = Field(..., description="Overall match score as percentage (0-100)")
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    match_explanation: str
    recommendation: str = Field(..., description="highly_recommended|recommended|potential_fit|not_recommended")
    compatibility: Optional[Dict[str, Any]] = Field(None, description="Detailed compatibility report")

class JobMatchList(BaseModel):
    """
    Schema for a list of job matches.
    """
    document_id: int
    matches: List[JobMatchResult]
    count: int

class CandidateMatchResult(BaseModel):
    """
    Schema for a single candidate match result when searching for candidates for a job.
    """
    candidate_id: int  # This maps to parsed_cv_id or document_id depending on use case, typically parsing_cv.id for access to details
    document_id: int
    name: Optional[str] = "Unknown Candidate"
    similarity_score: float = Field(..., description="0-1 Semantic similarity score", ge=0.0, le=1.0)
    skill_match_score: float = Field(..., description="0-1 Skill overlap score", ge=0.0, le=1.0)
    experience_match_score: float = Field(..., description="0-1 Experience level match score", ge=0.0, le=1.0)
    overall_match_score: float = Field(..., description="Weighted average of all scores", ge=0.0, le=1.0)
    match_percentage: int = Field(..., description="Overall match score as percentage (0-100)")
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    match_explanation: str
    recommendation: str = Field(..., description="highly_recommended|recommended|potential_fit|not_recommended")

class CandidateMatchList(BaseModel):
    """
    Schema for a list of candidate matches.
    """
    job_id: int
    matches: List[CandidateMatchResult]
    count: int
