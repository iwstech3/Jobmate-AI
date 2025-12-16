from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any

from app.models.job_post import JobPost
from app.models.job_view import JobView
from app.models.application import Application
from app.models.saved_job import SavedJob
from fastapi import HTTPException, status

def track_job_view(
    db: Session,
    job_post_id: int,
    viewer_email: Optional[str] = None,
    viewer_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    referrer: Optional[str] = None
) -> JobView:
    """
    Track a job view.
    1. Create JobView record
    2. Increment job_posts.views_count
    """
    # Verify job exists
    job = db.query(JobPost).filter(JobPost.id == job_post_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job post not found")

    # Optional: Logic to prevent duplicate view counting for anonymous users (e.g. 24h cooldown)
    # For now, we track every hit as requested, but maybe just check if duplicate in last 5 mins?
    # keeping it simple: track all.

    new_view = JobView(
        job_post_id=job_post_id,
        viewer_email=viewer_email,
        viewer_ip=viewer_ip,
        user_agent=user_agent,
        referrer=referrer
    )
    db.add(new_view)
    
    # Increment counter
    job.views_count += 1
    
    db.commit()
    db.refresh(new_view)
    return new_view

def increment_applications_count(db: Session, job_post_id: int):
    """Increment applications count for a job"""
    job = db.query(JobPost).filter(JobPost.id == job_post_id).first()
    if job:
        job.applications_count += 1
        db.commit()

def increment_saves_count(db: Session, job_post_id: int):
    """Increment saves count for a job"""
    job = db.query(JobPost).filter(JobPost.id == job_post_id).first()
    if job:
        job.saves_count += 1
        db.commit()

def decrement_saves_count(db: Session, job_post_id: int):
    """Decrement saves count for a job"""
    job = db.query(JobPost).filter(JobPost.id == job_post_id).first()
    if job and job.saves_count > 0:
        job.saves_count -= 1
        db.commit()

def get_job_stats(db: Session, job_post_id: int) -> Dict[str, Any]:
    """Get comprehensive stats for a job"""
    job = db.query(JobPost).filter(JobPost.id == job_post_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job post not found")
        
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    
    # Calculate last 7 days metrics
    views_7d = db.query(JobView).filter(
        JobView.job_post_id == job_post_id,
        JobView.viewed_at >= seven_days_ago
    ).count()
    
    applications_7d = db.query(Application).filter(
        Application.job_post_id == job_post_id,
        Application.applied_at >= seven_days_ago
    ).count()
    
    saves_7d = db.query(SavedJob).filter(
        SavedJob.job_post_id == job_post_id,
        SavedJob.saved_at >= seven_days_ago
    ).count()
    
    return {
        "job_id": job.id,
        "views_count": job.views_count,
        "applications_count": job.applications_count,
        "saves_count": job.saves_count,
        "views_last_7_days": views_7d,
        "applications_last_7_days": applications_7d,
        "saves_last_7_days": saves_7d,
        "top_viewer_locations": [] # Placeholder for now
    }

def get_jobs_analytics(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    sort_by: str = "views_count"
) -> List[Dict[str, Any]]:
    """Get analytics overview for all jobs"""
    query = db.query(JobPost)
    
    if sort_by == "views_count":
        query = query.order_by(desc(JobPost.views_count))
    elif sort_by == "applications_count":
        query = query.order_by(desc(JobPost.applications_count))
    elif sort_by == "saves_count":
        query = query.order_by(desc(JobPost.saves_count))
    else:
        query = query.order_by(desc(JobPost.created_at))
        
    jobs = query.offset(skip).limit(limit).all()
    
    results = []
    for job in jobs:
        total_views = job.views_count
        app_rate = (job.applications_count / total_views) if total_views > 0 else 0.0
        save_rate = (job.saves_count / total_views) if total_views > 0 else 0.0
        
        results.append({
            "job_id": job.id,
            "job_title": job.title,
            "company": job.company,
            "created_at": job.created_at,
            "total_views": job.views_count,
            "total_applications": job.applications_count,
            "total_saves": job.saves_count,
            "application_rate": round(app_rate, 4),
            "save_rate": round(save_rate, 4),
            "status": job.status
        })
        
    return results

def get_trending_jobs(db: Session, limit: int = 10) -> List[JobPost]:
    """
    Get trending jobs based on views in the last 7 days.
    """
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    
    # Query to count views per job in last 7 days
    results = db.query(
        JobView.job_post_id, 
        func.count(JobView.id).label('recent_views')
    ).filter(
        JobView.viewed_at >= seven_days_ago
    ).group_by(
        JobView.job_post_id
    ).order_by(
        desc('recent_views')
    ).limit(limit).all()
    
    # Get the actual JobPost objects
    trending_ids = [r[0] for r in results]
    
    # Preserve order
    if not trending_ids:
        return []
        
    # In SQL, "IN" clause doesn't preserve order. 
    # We can fetch and then sort in python, or use order by case, but list is small.
    jobs = db.query(JobPost).filter(JobPost.id.in_(trending_ids)).all()
    job_map = {job.id: job for job in jobs}
    
    return [job_map[jid] for jid in trending_ids if jid in job_map]
