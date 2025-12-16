from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status
from typing import Optional, List
from datetime import datetime

from app.models.job_post import JobPost
from app.models.job_status_history import JobStatusHistory

def change_job_status(
    db: Session,
    job_id: int,
    new_status: str,
    reason: Optional[str] = None
) -> Optional[JobPost]:
    """
    Change the status of a job post and record history.
    
    Valid transitions:
    - draft -> published
    - published -> closed
    - closed -> published (reopen)
    - draft -> closed (cancel)
    
    Invalid:
    - published -> draft (cannot unpublish, must close)
    - closed -> draft (cannot revert)
    """
    job = db.query(JobPost).filter(JobPost.id == job_id).first()
    if not job:
        return None
        
    old_status = job.status
    
    # Validation logic
    if old_status == new_status:
        # No-op but valid
        return job
        
    if old_status == "published" and new_status == "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revert published job to draft. Close it instead."
        )
        
    if old_status == "closed" and new_status == "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revert closed job to draft. Reopen it instead."       
        )

    if new_status == "closed" and not reason:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reason is required when closing a job."
        )

    # Update status
    job.status = new_status
    
    # Record history
    history = JobStatusHistory(
        job_post_id=job.id,
        old_status=old_status,
        new_status=new_status,
        changed_reason=reason
    )
    db.add(history)
    db.commit()
    db.refresh(job)
    
    return job

def publish_job(db: Session, job_id: int) -> Optional[JobPost]:
    return change_job_status(db, job_id, "published", reason="Published by user")

def close_job(db: Session, job_id: int, reason: str) -> Optional[JobPost]:
    return change_job_status(db, job_id, "closed", reason=reason)

def reopen_job(db: Session, job_id: int) -> Optional[JobPost]:
    return change_job_status(db, job_id, "published", reason="Reopened by user")

def get_status_history(db: Session, job_id: int) -> List[JobStatusHistory]:
    return db.query(JobStatusHistory)\
             .filter(JobStatusHistory.job_post_id == job_id)\
             .order_by(desc(JobStatusHistory.changed_at))\
             .all()

def get_jobs_by_status(
    db: Session,
    status: str,
    skip: int = 0,
    limit: int = 10
) -> tuple[List[JobPost], int]:
    query = db.query(JobPost).filter(JobPost.status == status)
    total = query.count()
    jobs = query.order_by(desc(JobPost.created_at)).offset(skip).limit(limit).all()
    return jobs, total
