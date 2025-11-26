from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class JobPostBase(BaseModel):
    """Base schema with common fields"""
    title: str = Field(..., min_length=1, max_length=200, description="Job title")
    company: str = Field(..., min_length=1, max_length=200, description="Company name")
    location: Optional[str] = Field(None, max_length=200, description="Job location")
    job_type: Optional[str] = Field(None, max_length=50, description="Type of job (Full-time, Part-time, etc.)")
    description: str = Field(..., min_length=10, description="Job description")


class JobPostCreate(JobPostBase):
    """Schema for creating a new job post"""
    pass


class JobPostUpdate(BaseModel):
    """Schema for updating an existing job post - all fields optional"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    company: Optional[str] = Field(None, min_length=1, max_length=200)
    location: Optional[str] = Field(None, max_length=200)
    job_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, min_length=10)


class JobPostOut(JobPostBase):
    """Schema for job post responses"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Updated from orm_mode (Pydantic v2)


class JobPostList(BaseModel):
    """Schema for paginated job post lists"""
    jobs: list[JobPostOut]
    total: int
    page: int
    page_size: int
    total_pages: int