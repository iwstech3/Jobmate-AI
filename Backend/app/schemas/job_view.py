from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class JobViewCreate(BaseModel):
    """Schema for tracking a new job view"""
    job_post_id: int
    viewer_email: Optional[str] = None
    viewer_ip: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None

class JobViewOut(BaseModel):
    """Schema for job view output"""
    id: int
    job_post_id: int
    viewer_email: Optional[str] = None
    viewed_at: datetime

    class Config:
        from_attributes = True
