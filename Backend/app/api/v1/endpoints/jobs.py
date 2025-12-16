from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import Annotated, Optional, List
import math

from app.database.db import get_db
from app.schemas.job_post import (
    JobPostCreate,
    JobPostUpdate,
    JobPostOut,
    JobPostList,
    JobPostStats,
    JobPostAnalytics
)
from app.crud import job_post as crud
from app.crud import job_analytics as analytics_crud

router = APIRouter(prefix="/jobs", tags=["Job Posts"])


@router.post(
    "/",
    response_model=JobPostOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new job posting"
)
def create_job(
    job_data: JobPostCreate,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Create a new job posting with the following information:
    
    - **title**: Job title (required)
    - **company**: Company name (required)
    - **location**: Job location (optional)
    - **job_type**: Employment type like Full-time, Part-time (optional)
    - **description**: Detailed job description (required)
    """
    return crud.create_job_post(db, job_data)


@router.get(
    "/search",
    response_model=JobPostList,
    summary="Search and filter job postings"
)
def search_jobs(
    q: Annotated[Optional[str], Query(description="Search keyword")] = None,
    location: Annotated[Optional[str], Query(description="Filter by location")] = None,
    job_type: Annotated[Optional[str], Query(description="Filter by job type")] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 10,
    db: Annotated[Session, Depends(get_db)] = None
):
    """
    Search and filter job postings with multiple criteria.
    
    - **q**: Search keyword (searches in title, company, description)
    - **location**: Filter by location (partial match, case-insensitive)
    - **job_type**: Filter by job type (partial match, case-insensitive)
    - **page**: Page number (starts at 1)
    - **page_size**: Number of jobs per page (max 100)
    
    Examples:
    - `/jobs/search?q=backend` - Search for "backend"
    - `/jobs/search?location=Remote` - Filter by remote jobs
    - `/jobs/search?q=python&location=Remote&job_type=Full-time` - Combined search
    """
    skip = (page - 1) * page_size
    jobs, total = crud.search_job_posts(
        db, 
        query=q,
        location=location,
        job_type=job_type,
        skip=skip,
        limit=page_size
    )
    
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    return JobPostList(
        jobs=jobs,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get(
    "/",
    response_model=JobPostList,
    summary="Get all job postings with pagination"
)
def list_jobs(
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 10,
    db: Annotated[Session, Depends(get_db)] = None
):
    """
    Retrieve all job postings with pagination.
    
    - **page**: Page number (starts at 1)
    - **page_size**: Number of jobs per page (max 100)
    
    Returns a list of jobs with pagination metadata.
    """
    skip = (page - 1) * page_size
    jobs, total = crud.get_job_posts(db, skip=skip, limit=page_size)
    
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    return JobPostList(
        jobs=jobs,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get(
    "/trending",
    response_model=List[JobPostOut],
    summary="Get trending jobs"
)
def get_trending_jobs(
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
    db: Annotated[Session, Depends(get_db)] = None
):
    """
    Get trending jobs based on views in the last 7 days.
    """
    return analytics_crud.get_trending_jobs(db, limit=limit)

@router.get(
    "/{job_id}",
    response_model=JobPostOut,
    summary="Get a specific job posting by ID"
)
def get_job(
    job_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Retrieve a single job posting by its ID.
    
    - **job_id**: The unique identifier of the job post
    """
    job = crud.get_job_post(db, job_id)
    
    
    # Track view
    analytics_crud.track_job_view(
        db=db,
        job_post_id=job_id,
        viewer_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        referrer=request.headers.get("referer")
    )
    
    return job
    analytics_crud.track_job_view(
        db=db,
        job_post_id=job_id,
        viewer_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        referrer=request.headers.get("referer")
    )
    
    return job

@router.get(
    "/{job_id}/stats",
    response_model=JobPostStats,
    summary="Get statistics for a specific job"
)
def get_job_stats(
    job_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Get detailed statistics for a job including views, applications, and saves.
    """
    return analytics_crud.get_job_stats(db, job_id)


@router.get(
    "/{job_id}/analytics",
    response_model=JobPostAnalytics,
    summary="Get analytics overview for a specific job"
)
def get_job_analytics(
    job_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Get analytics overview for a specific job.
    """
    stats = analytics_crud.get_job_stats(db, job_id)
    job = crud.get_job_post(db, job_id)
    
    if not job:
         raise HTTPException(status_code=404, detail="Job not found")

    total_views = job.views_count
    app_rate = (job.applications_count / total_views) if total_views > 0 else 0.0
    save_rate = (job.saves_count / total_views) if total_views > 0 else 0.0

    return JobPostAnalytics(
        job_id=job.id,
        job_title=job.title,
        company=job.company,
        created_at=job.created_at,
        total_views=job.views_count,
        total_applications=job.applications_count,
        total_saves=job.saves_count,
        application_rate=round(app_rate, 4),
        save_rate=round(save_rate, 4),
        status=job.status
    )



@router.put(
    "/{job_id}",
    response_model=JobPostOut,
    summary="Update an existing job posting"
)
def update_job(
    job_id: int,
    job_data: JobPostUpdate,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Update an existing job posting. Only provided fields will be updated.
    
    - **job_id**: The unique identifier of the job post
    - Provide only the fields you want to update
    """
    updated_job = crud.update_job_post(db, job_id, job_data)
    
    if not updated_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job post with id {job_id} not found"
        )
    
    return updated_job


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a job posting"
)
def delete_job(
    job_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Delete a job posting by its ID.
    
    - **job_id**: The unique identifier of the job post to delete
    """
    deleted = crud.delete_job_post(db, job_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job post with id {job_id} not found"
        )
    
    return None  # 204 No Content