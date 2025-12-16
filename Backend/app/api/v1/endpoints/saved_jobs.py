from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.database.db import get_db
from app.schemas.saved_job import (
    SavedJobCreate, 
    SavedJobOut, 
    SavedJobList, 
    SavedJobUpdate, 
    SavedJobWithDetails
)
from app.crud import saved_job as crud_saved_job

router = APIRouter(
    prefix="/saved-jobs",
    tags=["Saved Jobs"]
)

@router.post("/", response_model=SavedJobOut, status_code=status.HTTP_201_CREATED)
def save_job(
    saved_job_in: SavedJobCreate,
    db: Session = Depends(get_db)
):
    """
    Save a job for later viewing.
    """
    return crud_saved_job.save_job(db=db, save_data=saved_job_in)

@router.get("/", response_model=SavedJobList)
def get_saved_jobs(
    user_email: str = Query(..., description="User email to filter saved jobs"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of saved jobs for a user.
    """
    skip = (page - 1) * page_size
    items, total = crud_saved_job.get_saved_jobs(
        db=db, 
        user_email=user_email,
        skip=skip, 
        limit=page_size
    )
    
    # Transform to SavedJobWithDetails
    detailed_items = []
    for item in items:
        detailed_items.append(
            SavedJobWithDetails(
                saved_job=SavedJobOut.model_validate(item),
                job_title=item.job_post.title if item.job_post else "Unknown Job",
                company=item.job_post.company if item.job_post else "Unknown Company",
                location=item.job_post.location if item.job_post else None,
                job_type=item.job_post.job_type if item.job_post else None,
                posted_at=item.job_post.created_at if item.job_post else item.created_at
            )
        )
            
    return SavedJobList(
        items=detailed_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )

@router.get("/check/{job_post_id}")
def check_if_saved(
    job_post_id: int,
    user_email: str = Query(..., description="User email"),
    db: Session = Depends(get_db)
):
    """
    Check if a specific job is saved by the user.
    """
    saved_job = crud_saved_job.get_saved_job_by_job_id(db, job_post_id, user_email)
    return {
        "is_saved": saved_job is not None,
        "saved_job_id": saved_job.id if saved_job else None
    }

@router.get("/{saved_job_id}", response_model=SavedJobWithDetails)
def get_saved_job(
    saved_job_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single saved job by ID with details.
    """
    item = crud_saved_job.get_saved_job(db, saved_job_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved job not found"
        )
        
    return SavedJobWithDetails(
        saved_job=SavedJobOut.model_validate(item),
        job_title=item.job_post.title if item.job_post else "Unknown Job",
        company=item.job_post.company if item.job_post else "Unknown Company",
        location=item.job_post.location if item.job_post else None,
        job_type=item.job_post.job_type if item.job_post else None,
        posted_at=item.job_post.created_at if item.job_post else item.created_at
    )

@router.put("/{saved_job_id}/notes", response_model=SavedJobOut)
def update_saved_job_notes(
    saved_job_id: int,
    update_data: SavedJobUpdate,
    db: Session = Depends(get_db)
):
    """
    Update notes for a saved job.
    """
    # Note: user_email verification is tricky here as it's not passed in body or query generally for PUT.
    # In real auth system, we'd use current_user.
    # For now, we assume if they have the ID, they can update it, OR we could require email in body/query.
    # Given requirements didn't specify strict auth for update, I'll proceed without email check for this endpoint
    # to be consistent with simple MVP, but DELETE has explicit email check requirement.
    
    updated_item = crud_saved_job.update_saved_job_notes(
        db, 
        saved_job_id, 
        update_data.notes if update_data.notes else ""
    )
    
    if not updated_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved job not found"
        )
        
    return updated_item

@router.delete("/unsave/{job_post_id}", status_code=status.HTTP_204_NO_CONTENT)
def unsave_job_by_job_id(
    job_post_id: int,
    user_email: str = Query(..., description="User email for verification"),
    db: Session = Depends(get_db)
):
    """
    Unsave a job by job ID (convenience endpoint).
    """
    success = crud_saved_job.unsave_job_by_job_id(db, job_post_id, user_email)
    if not success:
        # Could be not found or not saved by user.
        # Idempotency suggests 204 if already gone, but 404 is often used if resource expected.
        # Requirements imply "Returns 404 if not found".
        # Let's check existence first if we want strict errors, but unsave usually implies "ensure not saved".
        # I'll return 404 to be specific as per requirements.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved job not found or not owned by user"
        )
    return None

@router.delete("/{saved_job_id}", status_code=status.HTTP_204_NO_CONTENT)
def unsave_job(
    saved_job_id: int,
    user_email: str = Query(..., description="User email for verification"),
    db: Session = Depends(get_db)
):
    """
    Delete a saved job entry.
    """
    # First check existence to distiguish 404 vs 403
    existing = crud_saved_job.get_saved_job(db, saved_job_id)
    if not existing:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved job not found"
        )
        
    if existing.user_email != user_email:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own saved jobs"
        )

    success = crud_saved_job.unsave_job(db, saved_job_id, user_email)
    if not success:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved job not found"
        )
    return None
