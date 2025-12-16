from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from fastapi import HTTPException, status
from typing import List, Optional, Tuple

from app.models.saved_job import SavedJob
from app.models.job_post import JobPost
from app.schemas.saved_job import SavedJobCreate
from app.crud.job_analytics import increment_saves_count, decrement_saves_count

def save_job(db: Session, save_data: SavedJobCreate) -> SavedJob:
    # 1. Validate Job Exists
    job = db.query(JobPost).filter(JobPost.id == save_data.job_post_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Job post with ID {save_data.job_post_id} not found"
        )

    # 2. Check if already saved
    if check_if_saved(db, save_data.job_post_id, save_data.user_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Job already saved"
        )

    # 3. Create SavedJob
    saved_job = SavedJob(
        job_post_id=save_data.job_post_id,
        user_email=save_data.user_email,
        notes=save_data.notes
    )
    
    db.add(saved_job)
    db.commit()
    db.refresh(saved_job)
    
    # NEW: Increment saves count
    increment_saves_count(db, save_data.job_post_id)
    
    return saved_job

def get_saved_job(db: Session, saved_job_id: int) -> Optional[SavedJob]:
    return db.query(SavedJob).options(
        joinedload(SavedJob.job_post)
    ).filter(SavedJob.id == saved_job_id).first()

def get_saved_jobs(
    db: Session,
    user_email: str,
    skip: int = 0,
    limit: int = 10
) -> Tuple[List[SavedJob], int]:
    
    query = db.query(SavedJob).options(
        joinedload(SavedJob.job_post)
    ).filter(SavedJob.user_email == user_email)

    # Get total count
    total = query.count()

    # Apply sorting (newest saved first) and pagination
    query = query.order_by(desc(SavedJob.saved_at))
    saved_jobs = query.offset(skip).limit(limit).all()

    return saved_jobs, total

def check_if_saved(db: Session, job_post_id: int, user_email: str) -> bool:
    count = db.query(SavedJob).filter(
        SavedJob.job_post_id == job_post_id,
        SavedJob.user_email == user_email
    ).count()
    return count > 0

def get_saved_job_by_job_id(db: Session, job_post_id: int, user_email: str) -> Optional[SavedJob]:
    return db.query(SavedJob).filter(
        SavedJob.job_post_id == job_post_id,
        SavedJob.user_email == user_email
    ).first()

def update_saved_job_notes(
    db: Session,
    saved_job_id: int,
    notes: str
) -> Optional[SavedJob]:
    saved_job = db.query(SavedJob).filter(SavedJob.id == saved_job_id).first()
    if not saved_job:
        return None
        
    saved_job.notes = notes
    db.commit()
    db.refresh(saved_job)
    return saved_job

def unsave_job(db: Session, saved_job_id: int, user_email: str) -> bool:
    saved_job = db.query(SavedJob).filter(SavedJob.id == saved_job_id).first()
    if not saved_job:
        return False
    
    # Verify ownership
    if saved_job.user_email != user_email:
        # In this helper, we return False or raise exception. 
        # Since the caller is API, we can treat unauthorized as not found/false or handle outside.
        # But logically, verify ownership is part of controller's job which calls this service? 
        # Or this service method implies "unsave THIS user's job".
        # Let's enforce it here.
        return False
        
    db.delete(saved_job)
    
    # NEW: Decrement saves count
    decrement_saves_count(db, saved_job.job_post_id)
    
    db.commit()
    return True

def unsave_job_by_job_id(db: Session, job_post_id: int, user_email: str) -> bool:
    saved_job = get_saved_job_by_job_id(db, job_post_id, user_email)
    if not saved_job:
        return False
        
    db.delete(saved_job)
    
    # NEW: Decrement saves count
    decrement_saves_count(db, saved_job.job_post_id)
    
    db.commit()
    return True
