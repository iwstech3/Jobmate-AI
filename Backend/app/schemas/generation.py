from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CoverLetterGenerateRequest(BaseModel):
    job_id: int
    cv_id: int
    custom_instructions: Optional[str] = None

class CoverLetterResponse(BaseModel):
    id: int
    job_id: int
    parsed_cv_id: int
    content: str
    customization_notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class CVSummaryTailorRequest(BaseModel):
    job_id: int
    cv_id: int

class CVSummaryResponse(BaseModel):
    tailored_summary: str
