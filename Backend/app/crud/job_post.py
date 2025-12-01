from sqlalchemy.orm import Session
from typing import Optional
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
    skip: int = 0,
    limit: int = 10
) -> tuple[list[JobPost], int]:
    """
    Search and filter job posts.
    
    Args:
        db: Database session
        query: Search keyword (searches in title, company, description)
        location: Filter by location (case-insensitive partial match)
        job_type: Filter by job type (case-insensitive partial match)
        skip: Number of records to skip (offset)
        limit: Maximum number of records to return
        
    Returns:
        Tuple of (list of JobPost objects, total count)
    """
    # Start with base query
    db_query = db.query(JobPost)
    
    # Apply keyword search if provided
    if query:
        # Case-insensitive search in title, company, and description
        search_filter = (
            JobPost.title.ilike(f"%{query}%") |
            JobPost.company.ilike(f"%{query}%") |
            JobPost.description.ilike(f"%{query}%")
        )
        db_query = db_query.filter(search_filter)
    
    # Apply location filter if provided
    if location:
        db_query = db_query.filter(JobPost.location.ilike(f"%{location}%"))
    
    # Apply job_type filter if provided
    if job_type:
        db_query = db_query.filter(JobPost.job_type.ilike(f"%{job_type}%"))
    
    # Get total count before pagination
    total = db_query.count()
    
    # Apply ordering and pagination
    # Order by relevance: exact matches in title first, then by date
    if query:
        # Prioritize jobs with query in title
        db_query = db_query.order_by(
            JobPost.title.ilike(f"%{query}%").desc(),
            JobPost.created_at.desc()
        )
    else:
        db_query = db_query.order_by(JobPost.created_at.desc())
    
    jobs = db_query.offset(skip).limit(limit).all()
    
    return jobs, total