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