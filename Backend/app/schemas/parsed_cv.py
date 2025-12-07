from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Any
from datetime import datetime

class WorkExperience(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None

class Education(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[str] = None

class ParsedCVBase(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience_years: Optional[int] = None
    education: List[Education] = Field(default_factory=list)
    work_experience: List[WorkExperience] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    summary: Optional[str] = None

class ParsedCVCreate(ParsedCVBase):
    document_id: int
    raw_text: Optional[str] = None

class ParsedCVOut(ParsedCVBase):
    id: int
    document_id: int
    raw_text: Optional[str] = None
    parsed_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
