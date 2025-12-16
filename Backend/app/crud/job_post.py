from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc, extract
from typing import Optional, List
from datetime import datetime
from app.models.job_post import JobPost
from app.schemas.job_post import JobPostCreate, JobPostUpdate


def create_job_post(db: Session, job_data: JobPostCreate) -> JobPost:
    """
    Create a new job posting in the database.
    
    Args:
        db: Database session
        job_data: Validated job post data from request
        
    Returns:
        Created JobPost instance
    """
    db_job = JobPost(**job_data.model_dump())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)  # Get the generated ID and timestamps
    return db_job


def get_job_post(db: Session, job_id: int) -> Optional[JobPost]:
    """
    Retrieve a single job post by ID.
    
    Args:
        db: Database session
        job_id: Job post ID
        
    Returns:
        JobPost if found, None otherwise
    """
    return db.query(JobPost).filter(JobPost.id == job_id).first()


def get_job_posts(
    db: Session, 
    skip: int = 0, 
    limit: int = 10
) -> tuple[list[JobPost], int]:
    """
    Retrieve all job posts with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip (offset)
        limit: Maximum number of records to return
        
    Returns:
        Tuple of (list of JobPost objects, total count)
    """
    query = db.query(JobPost)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination and ordering
    jobs = query.order_by(JobPost.created_at.desc()).offset(skip).limit(limit).all()
    
    return jobs, total


def update_job_post(
    db: Session, 
    job_id: int, 
    job_data: JobPostUpdate
) -> Optional[JobPost]:
    """
    Update an existing job post.
    
    Args:
        db: Database session
        job_id: Job post ID to update
        job_data: New data (only provided fields will be updated)
        
    Returns:
        Updated JobPost if found, None otherwise
    """
    db_job = get_job_post(db, job_id)
    
    if not db_job:
        return None
    
    # Update only the fields that were provided (not None)
    update_data = job_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_job, field, value)
    
    db.commit()
    db.refresh(db_job)
    return db_job


def delete_job_post(db: Session, job_id: int) -> bool:
    """
    Delete a job post by ID.
    
    Args:
        db: Database session
        job_id: Job post ID to delete
        
    Returns:
        True if deleted, False if not found
    """
    db_job = get_job_post(db, job_id)
    
    if not db_job:
        return False
    
    db.delete(db_job)
    db.commit()
    return True


def search_job_posts(
    db: Session,
    query: Optional[str] = None,
    location: Optional[str] = None,
    job_type: Optional[str] = None,
    company: Optional[str] = None,
    status: Optional[str] = "published",
    is_remote: Optional[bool] = None,
    is_featured: Optional[bool] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
    sort_by: Optional[str] = "created_at",
    sort_order: Optional[str] = "desc",
    skip: int = 0,
    limit: int = 10
) -> tuple[list[JobPost], int]:
    """
    Search and filter job posts with advanced options.
    """
    db_query = db.query(JobPost)
    
    # 1. Status Filter
    if status and status != "all":
        db_query = db_query.filter(JobPost.status == status)

    # 2. Keyword Search
    if query:
        search_filter = (
            JobPost.title.ilike(f"%{query}%") |
            JobPost.company.ilike(f"%{query}%") |
            JobPost.description.ilike(f"%{query}%")
        )
        db_query = db_query.filter(search_filter)
    
    # 3. Specific Filters
    if location:
        db_query = db_query.filter(JobPost.location.ilike(f"%{location}%"))
    
    if company:
        db_query = db_query.filter(JobPost.company.ilike(f"%{company}%"))

    if job_type:
        db_query = db_query.filter(JobPost.job_type.ilike(f"%{job_type}%"))
    
    # 4. Remote Filter
    if is_remote is not None:
        remote_keywords = ["remote", "télétravail", "distance", "work from home"]
        remote_filters = [JobPost.location.ilike(f"%{k}%") for k in remote_keywords]
        # Also check description for remote keywords if filtering for remote
        if is_remote:
             remote_filters.extend([JobPost.description.ilike(f"%{k}%") for k in remote_keywords])
             db_query = db_query.filter(or_(*remote_filters))
        else:
            # If is_remote=False, exclude jobs that strictly match remote in location
            # Note: Checking description for "NOT remote" is risky as it might say "Not remote" or "No remote work", so usually we strictly check location for "Remote"
            # For simplicity in this iteration: !location ILIKE remote
            not_remote_filters = [~JobPost.location.ilike(f"%{k}%") for k in remote_keywords]
            for f in not_remote_filters:
                db_query = db_query.filter(f)

    # 5. Boolean Filters
    if is_featured is not None:
        db_query = db_query.filter(JobPost.featured == is_featured)

    # 6. Date Range
    if created_after:
        db_query = db_query.filter(JobPost.created_at >= created_after)
    
    if created_before:
        db_query = db_query.filter(JobPost.created_at <= created_before)

    # Get total count before pagination
    total = db_query.count()
    
    # 7. Sorting
    sort_column = JobPost.created_at # Default
    
    if sort_by == "views_count":
        sort_column = JobPost.views_count
    elif sort_by == "applications_count":
        sort_column = JobPost.applications_count
    elif sort_by == "title":
        sort_column = JobPost.title
    elif sort_by == "company":
        sort_column = JobPost.company
    
    if sort_order == "asc":
        db_query = db_query.order_by(asc(sort_column))
    else:
        db_query = db_query.order_by(desc(sort_column))
    
    # Always add secondary sort by ID to ensure consistent paging
    db_query = db_query.order_by(desc(JobPost.id))
    
    jobs = db_query.offset(skip).limit(limit).all()
    
    return jobs, total