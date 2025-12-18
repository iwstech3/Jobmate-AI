"""
CRUD operations for CV Analysis
"""

from sqlalchemy.orm import Session
from app.models.cv_analysis import CVAnalysis
from app.schemas.cv_analysis import CVAnalysisCreate
from typing import Optional


def create_cv_analysis(db: Session, analysis_data: CVAnalysisCreate) -> CVAnalysis:
    """
    Create a new CV analysis record.
    
    Args:
        db: Database session
        analysis_data: CV analysis data to save
        
    Returns:
        Created CVAnalysis object
    """
    # Convert Pydantic models to dicts for JSON fields
    db_analysis = CVAnalysis(
        parsed_cv_id=analysis_data.parsed_cv_id,
        overall_score=analysis_data.overall_score,
        completeness_score=analysis_data.completeness_score,
        quality_score=analysis_data.quality_score,
        ats_score=analysis_data.ats_score,
        strengths=analysis_data.strengths,
        weaknesses=analysis_data.weaknesses,
        suggestions=[s.dict() for s in analysis_data.suggestions],
        skill_analysis=analysis_data.skill_analysis.dict(),
        experience_analysis=analysis_data.experience_analysis.dict()
    )
    
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    
    return db_analysis


def get_cv_analysis_by_parsed_cv_id(db: Session, parsed_cv_id: int) -> Optional[CVAnalysis]:
    """
    Get CV analysis by parsed CV ID.
    
    Args:
        db: Database session
        parsed_cv_id: ID of the parsed CV
        
    Returns:
        CVAnalysis object if found, None otherwise
    """
    return db.query(CVAnalysis).filter(CVAnalysis.parsed_cv_id == parsed_cv_id).first()


def get_cv_analysis(db: Session, analysis_id: int) -> Optional[CVAnalysis]:
    """
    Get CV analysis by ID.
    
    Args:
        db: Database session
        analysis_id: ID of the analysis
        
    Returns:
        CVAnalysis object if found, None otherwise
    """
    return db.query(CVAnalysis).filter(CVAnalysis.id == analysis_id).first()
