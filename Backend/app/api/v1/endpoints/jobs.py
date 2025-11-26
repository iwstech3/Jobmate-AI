from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Annotated
import math

from app.database.db import get_db
from app.schemas.job_post import (
    JobPostCreate,
    JobPostUpdate,
    JobPostOut,
    JobPostList
)
from app.crud import job_post as crud

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
    "/{job_id}",
    response_model=JobPostOut,
    summary="Get a specific job posting by ID"
)
def get_job(
    job_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Retrieve a single job posting by its ID.
    
    - **job_id**: The unique identifier of the job post
    """
    job = crud.get_job_post(db, job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job post with id {job_id} not found"
        )
    
    return job


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