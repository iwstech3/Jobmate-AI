from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
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


    # Analytics & Tracking
    views_count: int = 0
    applications_count: int = 0
    saves_count: int = 0
    status: str
    expires_at: Optional[datetime] = None
    featured: bool = False

    class Config:
        from_attributes = True  # Updated from orm_mode (Pydantic v2)


class JobPostStats(BaseModel):
    """Schema for job statistics"""
    job_id: int
    views_count: int
    applications_count: int
    saves_count: int
    views_last_7_days: int
    applications_last_7_days: int
    saves_last_7_days: int
    top_viewer_locations: List[Dict[str, Any]] = []


class JobPostAnalytics(BaseModel):
    """Schema for job analytics overview"""
    job_id: int
    job_title: str
    company: str
    created_at: datetime
    total_views: int
    total_applications: int
    total_saves: int
    application_rate: float
    save_rate: float
    status: str


class JobPostList(BaseModel):
    """Schema for paginated job post lists"""
    jobs: list[JobPostOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class JobSearchFilters(BaseModel):
    """Schema for advanced job search filters"""
    q: Optional[str] = Field(None, description="Keyword search")
    location: Optional[str] = Field(None, description="Filter by location")
    job_type: Optional[str] = Field(None, description="Filter by job type")
    company: Optional[str] = Field(None, description="Filter by company")
    status: Optional[Literal["published", "closed", "draft"]] = "published"
    sort_by: Optional[Literal["created_at", "views_count", "applications_count", "title", "company"]] = "created_at"
    sort_order: Optional[Literal["asc", "desc"]] = "desc"
    is_remote: Optional[bool] = None
    is_featured: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)


class JobSearchResult(JobPostList):
    """Enhanced search result with filter metadata"""
    filters_applied: Dict[str, Any]
    available_filters: Optional[Dict[str, Any]] = None