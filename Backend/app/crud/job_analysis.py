"""
CRUD operations for Job Analysis
"""

from sqlalchemy.orm import Session
from app.models.job_analysis import JobAnalysis
from app.schemas.job_analysis import JobAnalysisCreate
from typing import Optional


def create_job_analysis(db: Session, analysis_data: JobAnalysisCreate) -> JobAnalysis:
    """
    Create a new job analysis record.
    
    Args:
        db: Database session
        analysis_data: Job analysis data to save
        
    Returns:
        Created JobAnalysis object
    """
    # Convert Pydantic models to dicts for JSON fields
    db_analysis = JobAnalysis(
        job_post_id=analysis_data.job_post_id,
        required_skills=analysis_data.required_skills,
        preferred_skills=analysis_data.preferred_skills,
        experience_level=analysis_data.experience_level,
        min_years_experience=analysis_data.min_years_experience,
        max_years_experience=analysis_data.max_years_experience,
        education_requirements=analysis_data.education_requirements,
        certifications=analysis_data.certifications,
        responsibilities=analysis_data.responsibilities,
        benefits=analysis_data.benefits,
        salary_range=analysis_data.salary_range.dict() if analysis_data.salary_range else None,
        employment_type=analysis_data.employment_type,
        remote_policy=analysis_data.remote_policy,
        industry=analysis_data.industry,
        company_size=analysis_data.company_size,
        key_technologies=analysis_data.key_technologies,
        soft_skills=analysis_data.soft_skills
    )
    
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    
    return db_analysis


def get_job_analysis(db: Session, analysis_id: int) -> Optional[JobAnalysis]:
    """
    Get job analysis by ID.
    
    Args:
        db: Database session
        analysis_id: ID of the analysis
        
    Returns:
        JobAnalysis object if found, None otherwise
    """
    return db.query(JobAnalysis).filter(JobAnalysis.id == analysis_id).first()


def get_job_analysis_by_job_id(db: Session, job_post_id: int) -> Optional[JobAnalysis]:
    """
    Get job analysis by job post ID.
    
    Args:
        db: Database session
        job_post_id: ID of the job post
        
    Returns:
        JobAnalysis object if found, None otherwise
    """
    return db.query(JobAnalysis).filter(JobAnalysis.job_post_id == job_post_id).first()


def update_job_analysis(db: Session, job_post_id: int, analysis_data: JobAnalysisCreate) -> Optional[JobAnalysis]:
    """
    Update an existing job analysis.
    
    Args:
        db: Database session
        job_post_id: ID of the job post
        analysis_data: Updated analysis data
        
    Returns:
        Updated JobAnalysis object if found, None otherwise
    """
    db_analysis = get_job_analysis_by_job_id(db, job_post_id)
    
    if not db_analysis:
        return None
    
    # Update fields
    db_analysis.required_skills = analysis_data.required_skills
    db_analysis.preferred_skills = analysis_data.preferred_skills
    db_analysis.experience_level = analysis_data.experience_level
    db_analysis.min_years_experience = analysis_data.min_years_experience
    db_analysis.max_years_experience = analysis_data.max_years_experience
    db_analysis.education_requirements = analysis_data.education_requirements
    db_analysis.certifications = analysis_data.certifications
    db_analysis.responsibilities = analysis_data.responsibilities
    db_analysis.benefits = analysis_data.benefits
    db_analysis.salary_range = analysis_data.salary_range.dict() if analysis_data.salary_range else None
    db_analysis.employment_type = analysis_data.employment_type
    db_analysis.remote_policy = analysis_data.remote_policy
    db_analysis.industry = analysis_data.industry
    db_analysis.company_size = analysis_data.company_size
    db_analysis.key_technologies = analysis_data.key_technologies
    db_analysis.soft_skills = analysis_data.soft_skills
    
    db.commit()
    db.refresh(db_analysis)
    
    return db_analysis
