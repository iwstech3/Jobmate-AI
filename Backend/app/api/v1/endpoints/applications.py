from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.db import get_db
from app.schemas.application import (
    ApplicationCreate, 
    ApplicationOut, 
    ApplicationList, 
    ApplicationUpdate,
    ApplicationWithDetails,
    ApplicationStats
)
from app.crud import application as crud_application

router = APIRouter(
    prefix="/applications",
    tags=["Applications"]
)

@router.post("/", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def create_application(
    application_in: ApplicationCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new job application.
    Checks if job and documents exist, and if applicant has already applied.
    """
    return crud_application.create_application(db=db, application_data=application_in)

@router.get("/", response_model=ApplicationList)
def get_applications(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    job_post_id: Optional[int] = None,
    status: Optional[str] = None,
    applicant_email: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get paginated list of applications with optional filters.
    """
    skip = (page - 1) * page_size
    items, total = crud_application.get_applications(
        db=db, 
        skip=skip, 
        limit=page_size, 
        job_post_id=job_post_id,
        status=status,
        applicant_email=applicant_email
    )
    
    # Transform to ApplicationWithDetails
    # Note: Logic in crud returns Application objects (SQLAlchemy models),
    # Pydantic via from_attributes will handle conversation if structure matches.
    # However, ApplicationWithDetails expects flattened fields (job_title, etc.)
    # We need to manually construct the response items or handle it in Pydantic.
    # Let's construct it manually here for clarity and safety.
    
    detailed_items = []
    for app in items:
        detailed_items.append(
            ApplicationWithDetails(
                application=ApplicationOut.model_validate(app),
                job_title=app.job_post.title if app.job_post else "Unknown Job",
                company=app.job_post.company if app.job_post else "Unknown Company",
                cv_filename=app.cv_document.filename if app.cv_document else "Unknown File",
                cover_letter_filename=app.cover_letter_document.filename if app.cover_letter_document else None
            )
        )
            
    return ApplicationList(
        items=detailed_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )

@router.get("/stats", response_model=ApplicationStats)
def get_application_stats(
    job_post_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get application statistics (count by status).
    """
    return crud_application.get_application_stats(db=db, job_post_id=job_post_id)

@router.get("/{application_id}", response_model=ApplicationWithDetails)
def get_application(
    application_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single application by ID with full details.
    """
    app = crud_application.get_application(db=db, application_id=application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    return ApplicationWithDetails(
        application=ApplicationOut.model_validate(app),
        job_title=app.job_post.title if app.job_post else "Unknown Job",
        company=app.job_post.company if app.job_post else "Unknown Company",
        cv_filename=app.cv_document.filename if app.cv_document else "Unknown File",
        cover_letter_filename=app.cover_letter_document.filename if app.cover_letter_document else None
    )

@router.put("/{application_id}/status", response_model=ApplicationOut)
def update_application_status(
    application_id: int,
    status_update: ApplicationUpdate,
    db: Session = Depends(get_db)
):
    """
    Update application status and HR notes.
    """
    if not status_update.status:
         raise HTTPException(status_code=400, detail="Status is required")
         
    updated_app = crud_application.update_application_status(
        db=db,
        application_id=application_id,
        status=status_update.status,
        hr_notes=status_update.hr_notes
    )
    
    if not updated_app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    return updated_app

@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an application.
    """
    success = crud_application.delete_application(db=db, application_id=application_id)
    if not success:
        raise HTTPException(status_code=404, detail="Application not found")
    return None

@router.get("/jobs/{job_id}/applications", response_model=ApplicationList)
# This was requested as valid endpoint structure: GET /jobs/{job_id}/applications
# However, standard REST usually keeps resources together. But requirements asked for convenience endpoint.
# Since we already have filtering in GET /applications, this is just a specific route for it.
# Wait, this might be better placed in the applications router but with a different path,
# OR in the jobs router. The requirements said:
# "G. GET /jobs/{job_id}/applications" -> in "4. CREATE: app/api/v1/endpoints/applications.py"
# So I will put it here, but the path will be slightly awkward relative to prefix /applications.
# Actually, prefix is defined in main.py usually for the router.
# If I define it as @router.get("/jobs/{job_id}/applications") here, and router prefix is /applications,
# it becomes /applications/jobs/{job_id}/applications. That's probably not what was intended.
# The user requirement #4 says "CREATE: app/api/v1/endpoints/applications.py" and lists "GET /jobs/{job_id}/applications".
# This likely means I should add a specific route for this, but ideally it should be:
# GET /applications?job_post_id={job_id} which I already supported.
# I will adhere to the request but maybe put it as a separate root router or just implement it within the /applications prefix?
# Let's look at requirement 5: "UPDATE: app/api/v1/endpoints/__init__.py - Add applications router import"
# Requirement 6: "UPDATE: app/main.py - Include applications router with prefix /api/v1" 
# (Wait, usually prefix is /api/v1/applications).
# Let's check main.py again.
# app.include_router(jobs.router, prefix="/api/v1") <- jobs router likely has /jobs prefix inside it?
# Let's check jobs.py to see how they handle prefixes.
def get_job_applications(
    job_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all applications for a specific job.
    """
    # Just reuse the logic
    return get_applications(
        page=page, 
        page_size=page_size, 
        job_post_id=job_id, 
        status=status, 
        db=db
    )
