from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Annotated

from app.database.db import get_db
from app.schemas.generation import CoverLetterGenerateRequest, CoverLetterResponse, CVSummaryTailorRequest, CVSummaryResponse
from app.services.ai.generator_service import get_generator_service
from app.crud.generation import create_cover_letter, get_cover_letter, get_cover_letters
from app.crud.job_post import get_job
from app.crud.parsed_cv import get_parsed_cv_by_document_id

router = APIRouter(prefix="/generation", tags=["Generation"])

@router.post("/cover-letter", response_model=CoverLetterResponse, status_code=status.HTTP_201_CREATED)
async def generate_cl(
    request: CoverLetterGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    generator = Depends(get_generator_service)
):
    # 1. Verify Job
    job = get_job(db, request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # 2. Verify CV (using document_id as per request but we need ParsedCV)
    parsed_cv = get_parsed_cv_by_document_id(db, request.cv_id)
    if not parsed_cv:
        raise HTTPException(status_code=404, detail="Parsed CV not found. Please parse document first.")
    
    # 3. Generate
    try:
        content = await generator.generate_cover_letter(
            cv_text=parsed_cv.raw_text,
            job=job,
            custom_instructions=request.custom_instructions
        )
        
        # 4. Save
        cl_data = {
            "job_id": request.job_id,
            "parsed_cv_id": parsed_cv.id,
            "content": content,
            "customization_notes": request.custom_instructions
        }
        return create_cover_letter(db, cl_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cv-summary", response_model=CVSummaryResponse)
async def tailor_summary(
    request: CVSummaryTailorRequest,
    db: Annotated[Session, Depends(get_db)],
    generator = Depends(get_generator_service)
):
    job = get_job(db, request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    parsed_cv = get_parsed_cv_by_document_id(db, request.cv_id)
    if not parsed_cv:
        raise HTTPException(status_code=404, detail="Parsed CV not found")
        
    summary = await generator.tailor_cv_summary(parsed_cv.raw_text, job.description)
    return CVSummaryResponse(tailored_summary=summary)

@router.get("/cover-letters", response_model=List[CoverLetterResponse])
def list_cover_letters(
    skip: int = 0,
    limit: int = 10,
    db: Annotated[Session, Depends(get_db)] = None
):
    return get_cover_letters(db, skip=skip, limit=limit)

@router.get("/cover-letters/{cl_id}", response_model=CoverLetterResponse)
def read_cover_letter(cl_id: int, db: Annotated[Session, Depends(get_db)]):
    cl = get_cover_letter(db, cl_id)
    if not cl:
        raise HTTPException(status_code=404, detail="Cover letter not found")
    return cl
