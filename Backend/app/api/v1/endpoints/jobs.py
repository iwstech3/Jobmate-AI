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
    JobPostAnalytics,
    JobSearchResult
)
from app.crud import job_post as crud
from app.crud import job_analytics as analytics_crud
from app.crud import job_filters as filters_crud
from datetime import datetime

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
    "/filters/options",
    summary="Get available filter options"
)
def get_filter_options(
    db: Annotated[Session, Depends(get_db)]
):
    """
    Get available options for search filters (locations, companies, job types)
    and summary counts.
    """
    return {
        "locations": filters_crud.get_unique_locations(db),
        "companies": filters_crud.get_unique_companies(db),
        "job_types": filters_crud.get_unique_job_types(db),
        "counts": filters_crud.get_filter_counts(db)
    }

@router.get(
    "/search",
    response_model=JobSearchResult,
    summary="Search and filter job postings"
)
def search_jobs(
    q: Annotated[Optional[str], Query(description="Search keyword")] = None,
    location: Annotated[Optional[str], Query(description="Filter by location")] = None,
    job_type: Annotated[Optional[str], Query(description="Filter by job type")] = None,
    company: Annotated[Optional[str], Query(description="Filter by company")] = None,
    status: Annotated[str, Query(description="Filter by status (published, closed, all)")] = "published",
    is_remote: Annotated[Optional[bool], Query(description="Filter by remote status")] = None,
    is_featured: Annotated[Optional[bool], Query(description="Filter by featured status")] = None,
    created_after: Annotated[Optional[datetime], Query(description="Posted after date")] = None,
    created_before: Annotated[Optional[datetime], Query(description="Posted before date")] = None,
    sort_by: Annotated[str, Query(regex="^(created_at|views_count|applications_count|title|company)$")] = "created_at",
    sort_order: Annotated[str, Query(regex="^(asc|desc)$")] = "desc",
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 10,
    db: Annotated[Session, Depends(get_db)] = None
):
    """
    Search and filter job postings with multiple criteria.
    """
    skip = (page - 1) * page_size
    
    jobs, total = crud.search_job_posts(
        db, 
        query=q,
        location=location,
        job_type=job_type,
        company=company,
        status=status,
        is_remote=is_remote,
        is_featured=is_featured,
        created_after=created_after,
        created_before=created_before,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=page_size
    )
    
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    # Construct filters applied summary
    filters = {
        k: v for k, v in locals().items() 
        if k in ['q', 'location', 'job_type', 'company', 'status', 'is_remote', 'is_featured', 'sort_by'] 
        and v is not None
    }
    
    return JobSearchResult(
        jobs=jobs,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        filters_applied=filters
    )


@router.get(
    "/recent",
    response_model=JobPostList,
    summary="Get recently posted jobs"
)
def get_recent_jobs(
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    page: Annotated[int, Query(ge=1)] = 1,
    db: Annotated[Session, Depends(get_db)] = None
):
    """Get jobs posted recently (last 7 days by default via sort)"""
    return search_jobs(
        sort_by="created_at",
        sort_order="desc", 
        page=page, 
        page_size=limit, 
        db=db
    )

@router.get(
    "/featured",
    response_model=JobPostList,
    summary="Get featured jobs"
)
def get_featured_jobs(
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    page: Annotated[int, Query(ge=1)] = 1,
    db: Annotated[Session, Depends(get_db)] = None
):
    """Get featured jobs only"""
    return search_jobs(
        is_featured=True,
        sort_by="created_at",
        sort_order="desc",
        page=page,
        page_size=limit,
        db=db
    )

@router.get(
    "/by-location/{location}",
    response_model=JobPostList,
    summary="Get jobs by location"
)
def get_jobs_by_location(
    location: str,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    sort_by: Annotated[str, Query(regex="^(created_at|views_count|applications_count)$")] = "created_at",
    db: Annotated[Session, Depends(get_db)] = None
):
    """Get jobs in a specific location"""
    return search_jobs(
        location=location,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
        db=db
    )

@router.get(
    "/by-company/{company}",
    response_model=JobPostList,
    summary="Get jobs by company"
)
def get_jobs_by_company(
    company: str,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    db: Annotated[Session, Depends(get_db)] = None
):
    """Get jobs at a specific company"""
    return search_jobs(
        company=company,
        page=page,
        page_size=page_size,
        db=db
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