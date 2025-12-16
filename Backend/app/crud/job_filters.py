from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, or_
from typing import List, Dict, Any
from app.models.job_post import JobPost

def get_unique_locations(db: Session) -> List[str]:
    """Get list of unique job locations"""
    locations = db.query(distinct(JobPost.location)).filter(
        JobPost.location.isnot(None), 
        JobPost.status == 'published'
    ).order_by(JobPost.location).all()
    return [loc[0] for loc in locations if loc[0]]

def get_unique_companies(db: Session) -> List[str]:
    """Get list of unique companies"""
    companies = db.query(distinct(JobPost.company)).filter(
        JobPost.company.isnot(None),
        JobPost.status == 'published'
    ).order_by(JobPost.company).all()
    return [comp[0] for comp in companies if comp[0]]

def get_unique_job_types(db: Session) -> List[str]:
    """Get list of unique job types"""
    job_types = db.query(distinct(JobPost.job_type)).filter(
        JobPost.job_type.isnot(None),
        JobPost.status == 'published'
    ).order_by(JobPost.job_type).all()
    return [type[0] for type in job_types if type[0]]

def get_filter_counts(db: Session) -> Dict[str, int]:
    """Get summary counts for filters"""
    total_active = db.query(JobPost).filter(JobPost.status == 'published').count()
    
    remote_keywords = ["remote", "télétravail", "work from home", "distance"]
    remote_filters = [JobPost.location.ilike(f"%{k}%") for k in remote_keywords]
    remote_filters.extend([JobPost.description.ilike(f"%{k}%") for k in remote_keywords])
    
    remote_count = db.query(JobPost).filter(
        JobPost.status == 'published',
        or_(*remote_filters)
    ).count()
    
    featured_count = db.query(JobPost).filter(
        JobPost.status == 'published',
        JobPost.featured == True
    ).count()
    
    return {
        "total_active": total_active,
        "remote_count": remote_count,
        "featured_count": featured_count
    }
