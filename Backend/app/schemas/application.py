from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class ApplicationBase(BaseModel):
    applicant_name: str = Field(min_length=2, max_length=255)
    applicant_email: EmailStr
    applicant_phone: Optional[str] = Field(None, max_length=50)

class ApplicationCreate(ApplicationBase):
    job_post_id: int
    cv_document_id: int
    cover_letter_document_id: Optional[int] = None

class ApplicationUpdate(BaseModel):
    status: Optional[Literal["pending", "reviewed", "shortlisted", "rejected", "accepted"]] = None
    hr_notes: Optional[str] = None

class ApplicationOut(ApplicationBase):
    id: int
    job_post_id: int
    cv_document_id: int
    cover_letter_document_id: Optional[int] = None
    status: str
    applied_at: datetime
    reviewed_at: Optional[datetime] = None
    hr_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ApplicationWithDetails(BaseModel):
    application: ApplicationOut
    job_title: str
    company: str
    cv_filename: str
    cover_letter_filename: Optional[str] = None

    class Config:
        from_attributes = True

class ApplicationList(BaseModel):
    items: List[ApplicationWithDetails]
    total: int
    page: int
    page_size: int
    total_pages: int

class ApplicationStats(BaseModel):
    total_applications: int
    pending: int = 0
    reviewed: int = 0
    shortlisted: int = 0
    rejected: int = 0
    accepted: int = 0
