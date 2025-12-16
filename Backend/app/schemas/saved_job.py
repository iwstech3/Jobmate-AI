from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

class SavedJobCreate(BaseModel):
    job_post_id: int
    user_email: EmailStr
    notes: Optional[str] = None

class SavedJobUpdate(BaseModel):
    notes: Optional[str] = None

class SavedJobOut(BaseModel):
    id: int
    job_post_id: int
    user_email: EmailStr
    notes: Optional[str] = None
    saved_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SavedJobWithDetails(BaseModel):
    saved_job: SavedJobOut
    job_title: str
    company: str
    location: Optional[str] = None
    job_type: Optional[str] = None
    posted_at: datetime

    class Config:
        from_attributes = True

class SavedJobList(BaseModel):
    items: List[SavedJobWithDetails]
    total: int
    page: int
    page_size: int
    total_pages: int
