from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Annotated, Optional
import math

from app.database.db import get_db
from app.schemas.job_post import (
    JobPostCreate,
    JobPostUpdate,
    JobPostOut,
    JobPostList
)
from app.schemas.job_match import CandidateMatchList
from app.crud import job_post as crud

router = APIRouter(prefix="/jobs", tags=["Job Posts"])


@router.post(
    "/",
    response_model=JobPostOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new job posting"
)
def create_job(
    job_data: JobPostCreate,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Create a new job posting with the following information:
    
    - **title**: Job title (required)
    - **company**: Company name (required)
    - **location**: Job location (optional)
    - **job_type**: Employment type like Full-time, Part-time (optional)
    - **description**: Detailed job description (required)
    """
    return crud.create_job_post(db, job_data)


@router.get(
    "/search",
    response_model=JobPostList,
    summary="Search and filter job postings"
)
def search_jobs(
    q: Annotated[Optional[str], Query(description="Search keyword")] = None,
    location: Annotated[Optional[str], Query(description="Filter by location")] = None,
    job_type: Annotated[Optional[str], Query(description="Filter by job type")] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 10,
    db: Annotated[Session, Depends(get_db)] = None
):
    """
    Search and filter job postings with multiple criteria.
    
    - **q**: Search keyword (searches in title, company, description)
    - **location**: Filter by location (partial match, case-insensitive)
    - **job_type**: Filter by job type (partial match, case-insensitive)
    - **page**: Page number (starts at 1)
    - **page_size**: Number of jobs per page (max 100)
    
    Examples:
    - `/jobs/search?q=backend` - Search for "backend"
    - `/jobs/search?location=Remote` - Filter by remote jobs
    - `/jobs/search?q=python&location=Remote&job_type=Full-time` - Combined search
    """
    skip = (page - 1) * page_size
    jobs, total = crud.search_job_posts(
        db, 
        query=q,
        location=location,
        job_type=job_type,
        skip=skip,
        limit=page_size
    )
    
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    return JobPostList(
        jobs=jobs,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get(
    "/",
    response_model=JobPostList,
    summary="Get all job postings with pagination"
)
def list_jobs(
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 10,
    db: Annotated[Session, Depends(get_db)] = None
):
    """
    Retrieve all job postings with pagination.
    
    - **page**: Page number (starts at 1)
    - **page_size**: Number of jobs per page (max 100)
    
    Returns a list of jobs with pagination metadata.
    """
    skip = (page - 1) * page_size
    jobs, total = crud.get_job_posts(db, skip=skip, limit=page_size)
    
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    return JobPostList(
        jobs=jobs,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get(
    "/{job_id}",
    response_model=JobPostOut,
    summary="Get a specific job posting by ID"
)
def get_job(
    job_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Retrieve a single job posting by its ID.
    
    - **job_id**: The unique identifier of the job post
    """
    job = crud.get_job_post(db, job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job post with id {job_id} not found"
        )
    
    return job


@router.put(
    "/{job_id}",
    response_model=JobPostOut,
    summary="Update an existing job posting"
)
def update_job(
    job_id: int,
    job_data: JobPostUpdate,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Update an existing job posting. Only provided fields will be updated.
    
    - **job_id**: The unique identifier of the job post
    - Provide only the fields you want to update
    """
    updated_job = crud.update_job_post(db, job_id, job_data)
    
    if not updated_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job post with id {job_id} not found"
        )
    
    return updated_job


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a job posting"
)
def delete_job(
    job_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Delete a job posting by its ID.
    
    - **job_id**: The unique identifier of the job post to delete
    """
    deleted = crud.delete_job_post(db, job_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job post with id {job_id} not found"
        )
    
    return None  # 204 No Content


@router.post(
    "/{job_id}/analyze",
    response_model=None,  # Will use JobAnalysisOut
    status_code=status.HTTP_200_OK,
    summary="Analyze job description and extract requirements"
)
async def analyze_job(
    job_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Analyze a job posting and extract structured requirements and metadata.
    
    - **job_id**: Job post ID
    
    Returns comprehensive job analysis including:
    - Required and preferred skills
    - Experience level and years
    - Education requirements and certifications
    - Responsibilities and benefits
    - Salary range (if mentioned)
    - Employment type and remote policy
    - Key technologies and soft skills
    
    Also generates and stores semantic embedding for job-CV matching.
    """
    from app.services.ai.job_analyzer_service import get_job_analyzer_service
    from app.services.ai.embeddings_service import get_embeddings_service
    from app.crud.job_analysis import create_job_analysis, get_job_analysis_by_job_id
    from app.schemas.job_analysis import JobAnalysisCreate, JobAnalysisOut, SalaryRange
    from app.models.job_embedding import JobEmbedding
    
    # 1. Check if job exists
    job = crud.get_job_post(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job post with id {job_id} not found"
        )
    
    # 2. Check if already analyzed (return cached result)
    existing_analysis = get_job_analysis_by_job_id(db, job_id)
    if existing_analysis:
        return JobAnalysisOut.from_orm(existing_analysis)
    
    # 3. Analyze job
    analyzer_service = get_job_analyzer_service()
    try:
        analysis_result = analyzer_service.analyze_job(job)
        
        # 4. Convert to Pydantic models for validation
        salary_range = None
        if analysis_result.get("salary_range"):
            salary_range = SalaryRange(**analysis_result["salary_range"])
        
        # 5. Create analysis record
        analysis_create = JobAnalysisCreate(
            job_post_id=job_id,
            required_skills=analysis_result["required_skills"],
            preferred_skills=analysis_result["preferred_skills"],
            experience_level=analysis_result["experience_level"],
            min_years_experience=analysis_result.get("min_years_experience"),
            max_years_experience=analysis_result.get("max_years_experience"),
            education_requirements=analysis_result["education_requirements"],
            certifications=analysis_result["certifications"],
            responsibilities=analysis_result["responsibilities"],
            benefits=analysis_result["benefits"],
            salary_range=salary_range,
            employment_type=analysis_result["employment_type"],
            remote_policy=analysis_result.get("remote_policy"),
            industry=analysis_result.get("industry"),
            company_size=analysis_result.get("company_size"),
            key_technologies=analysis_result["key_technologies"],
            soft_skills=analysis_result["soft_skills"]
        )
        
        db_analysis = create_job_analysis(db, analysis_create)
        
        # 6. Generate and store embedding
        try:
            embeddings_service = get_embeddings_service()
            
            # Create embedding text from key job information
            embedding_text = f"{job.title}\n"
            embedding_text += f"Company: {job.company}\n"
            embedding_text += f"Required skills: {', '.join(analysis_result['required_skills'][:10])}\n"
            embedding_text += f"Responsibilities: {' '.join(analysis_result['responsibilities'][:3])}\n"
            embedding_text += f"Experience level: {analysis_result['experience_level']}"
            
            # Generate embedding vector
            embedding_vector = embeddings_service.embed_document(embedding_text)
            
            # Check if embedding already exists
            existing_embedding = db.query(JobEmbedding).filter(
                JobEmbedding.job_post_id == job_id
            ).first()
            
            if existing_embedding:
                # Update existing embedding
                existing_embedding.embedding = embedding_vector
                existing_embedding.embedded_text = embedding_text
            else:
                # Create new embedding
                job_embedding = JobEmbedding(
                    job_post_id=job_id,
                    embedding=embedding_vector,
                    embedded_text=embedding_text
                )
                db.add(job_embedding)
            
            db.commit()
            
        except Exception as e:
            # Log embedding error but don't fail the analysis
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to generate embedding for job {job_id}: {str(e)}")
        
        return JobAnalysisOut.from_orm(db_analysis)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during analysis: {str(e)}"
        )


@router.get(
    "/{job_id}/matching-candidates",
    response_model=CandidateMatchList,
    summary="Find matching candidates for a job"
)
def find_matching_candidates(
    job_id: int,
    limit: Annotated[int, Query(ge=1, le=50, description="Max results")] = 10,
    min_score: Annotated[float, Query(ge=0.0, le=1.0, description="Minimum match score")] = 0.5,
    db: Annotated[Session, Depends(get_db)] = None
):
    """
    Find matching candidates for a job using semantic search and rule-based scoring.
    """
    from app.services.ai.job_matcher_service import JobMatcherService

    # Check job
    job = crud.get_job_post(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job post not found."
        )

    matcher = JobMatcherService()
    matches = matcher.find_matching_candidates(db, job_id, limit, min_score)
    
    return CandidateMatchList(
        job_id=job_id,
        matches=matches,
        count=len(matches)
    )

