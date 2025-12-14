from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
from fastapi import HTTPException
from typing import List, Optional, Tuple, Dict, Any

from app.models.application import Application
from app.models.job_post import JobPost
from app.models.document import Document
from app.schemas.application import ApplicationCreate

def create_application(db: Session, application_data: ApplicationCreate) -> Application:
    # 1. Validate Job Exists
    job = db.query(JobPost).filter(JobPost.id == application_data.job_post_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job post with ID {application_data.job_post_id} not found")

    # 2. Validate Document Exists
    cv = db.query(Document).filter(Document.id == application_data.cv_document_id).first()
    if not cv:
         raise HTTPException(status_code=404, detail=f"CV document with ID {application_data.cv_document_id} not found")
    
    if application_data.cover_letter_document_id:
        cl = db.query(Document).filter(Document.id == application_data.cover_letter_document_id).first()
        if not cl:
             raise HTTPException(status_code=404, detail=f"Cover letter document with ID {application_data.cover_letter_document_id} not found")

    # 3. Check for Duplicate Application
    existing_application = db.query(Application).filter(
        Application.job_post_id == application_data.job_post_id,
        Application.applicant_email == application_data.applicant_email
    ).first()
    
    if existing_application:
        raise HTTPException(status_code=400, detail="Applicant has already applied for this job.")

    # 4. Create Application
    db_application = Application(
        job_post_id=application_data.job_post_id,
        applicant_name=application_data.applicant_name,
        applicant_email=application_data.applicant_email,
        applicant_phone=application_data.applicant_phone,
        cv_document_id=application_data.cv_document_id,
        cover_letter_document_id=application_data.cover_letter_document_id,
        status="pending"
    )
    
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application

def get_application(db: Session, application_id: int) -> Optional[Application]:
    return db.query(Application).options(
        joinedload(Application.job_post),
        joinedload(Application.cv_document),
        joinedload(Application.cover_letter_document)
    ).filter(Application.id == application_id).first()

def get_applications(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    job_post_id: Optional[int] = None,
    status: Optional[str] = None,
    applicant_email: Optional[str] = None
) -> Tuple[List[Application], int]:
    
    query = db.query(Application).options(
        joinedload(Application.job_post),
        joinedload(Application.cv_document),
        joinedload(Application.cover_letter_document)
    )

    if job_post_id:
        query = query.filter(Application.job_post_id == job_post_id)
    
    if status:
        query = query.filter(Application.status == status)
        
    if applicant_email:
        query = query.filter(Application.applicant_email.ilike(f"%{applicant_email}%"))

    # Get total count before pagination
    total = query.count()

    # Apply sorting (newest first) and pagination
    query = query.order_by(desc(Application.applied_at))
    applications = query.offset(skip).limit(limit).all()

    return applications, total

def update_application_status(
    db: Session,
    application_id: int,
    status: str,
    hr_notes: Optional[str] = None
) -> Optional[Application]:
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        return None

    # Update logic
    old_status = application.status
    application.status = status
    
    if hr_notes is not None:
        application.hr_notes = hr_notes
        
    # Set reviewed_at if moving from pending and not already set
    if old_status == "pending" and status != "pending" and not application.reviewed_at:
        application.reviewed_at = func.now()

    db.commit()
    db.refresh(application)
    return application

def delete_application(db: Session, application_id: int) -> bool:
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        return False
        
    db.delete(application)
    db.commit()
    return True

def get_application_stats(db: Session, job_post_id: Optional[int] = None) -> Dict[str, Any]:
    query = db.query(Application.status, func.count(Application.status))
    
    if job_post_id:
        query = query.filter(Application.job_post_id == job_post_id)
        
    results = query.group_by(Application.status).all()
    
    stats = {
        "total_applications": 0,
        "pending": 0,
        "reviewed": 0,
        "shortlisted": 0,
        "rejected": 0,
        "accepted": 0
    }
    
    for status, count in results:
        stats[status] = count
        stats["total_applications"] += count
        
    return stats
