from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Annotated, List, Dict, Any
from datetime import datetime, timezone, timedelta

from app.database.db import get_db
from app.models.job_post import JobPost
from app.models.application import Application
from app.models.job_view import JobView
from app.schemas.job_post import JobPostAnalytics

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard", summary="Get platform-wide analytics overview")
def get_analytics_dashboard(
    db: Annotated[Session, Depends(get_db)]
):
    """
    Get high-level platform statistics.
    """
    now = datetime.now(timezone.utc)
    start_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    
    total_jobs = db.query(JobPost).count()
    active_jobs = db.query(JobPost).filter(JobPost.status == "published").count()
    total_applications = db.query(Application).count()
    total_views = db.query(JobView).count()
    
    jobs_this_month = db.query(JobPost).filter(JobPost.created_at >= start_of_month).count()
    applications_this_month = db.query(Application).filter(Application.applied_at >= start_of_month).count()
    
    return {
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "total_applications": total_applications,
        "total_views": total_views,
        "jobs_this_month": jobs_this_month,
        "applications_this_month": applications_this_month
    }

@router.get("/jobs/top-performing", response_model=List[JobPostAnalytics], summary="Get top performing jobs by application rate")
def get_top_performing_jobs(
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    db: Annotated[Session, Depends(get_db)] = None
):
    """
    Get top jobs sorted by application rate (applications / views).
    Only includes jobs with at least 1 view.
    """
    # Fetch jobs with at least 1 view
    jobs = db.query(JobPost).filter(JobPost.views_count > 0).all()
    
    # Calculate rates in python (easier than complex SQL for now)
    job_stats = []
    for job in jobs:
        total_views = job.views_count
        app_rate = (job.applications_count / total_views) if total_views > 0 else 0.0
        save_rate = (job.saves_count / total_views) if total_views > 0 else 0.0
        
        job_stats.append({
            "job": job,
            "app_rate": app_rate,
            "save_rate": save_rate
        })
    
    # Sort by app_rate desc
    job_stats.sort(key=lambda x: x["app_rate"], reverse=True)
    
    # Take top N
    top_jobs = job_stats[:limit]
    
    return [
        JobPostAnalytics(
            job_id=item["job"].id,
            job_title=item["job"].title,
            company=item["job"].company,
            created_at=item["job"].created_at,
            total_views=item["job"].views_count,
            total_applications=item["job"].applications_count,
            total_saves=item["job"].saves_count,
            application_rate=round(item["app_rate"], 4),
            save_rate=round(item["save_rate"], 4),
            status=item["job"].status
        )
        for item in top_jobs
    ]
