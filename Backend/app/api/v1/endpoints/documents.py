from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Annotated, Optional
import math

from app.database.db import get_db
from app.schemas.document import DocumentCreate, DocumentOut, DocumentUploadResponse
from app.schemas.parsed_cv import ParsedCVOut
from app.schemas.job_match import JobMatchList
from app.crud import document as crud
from app.utils import file_storage

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document (CV, resume, cover letter)"
)
async def upload_document(
    file: Annotated[UploadFile, File(description="Document file (PDF, DOCX, DOC, TXT)")],
    document_type: Annotated[Optional[str], Query(description="Type: cv, cover_letter, certificate")] = None,
    db: Annotated[Session, Depends(get_db)] = None
):
    """
    Upload a document file.
    
    - **file**: Document file (max 10MB)
    - **document_type**: Optional type classification (cv, cover_letter, certificate, etc.)
    
    Supported formats: PDF, DOCX, DOC, TXT
    
    Returns document metadata and download URL.
    """
    # Save file to storage
    stored_filename, file_path, file_size = await file_storage.save_upload_file(file)
    
    # Create database record
    doc_data = DocumentCreate(
        filename=file.filename,
        stored_filename=stored_filename,
        file_path=file_path,
        file_type=file.content_type,
        file_size=file_size,
        document_type=document_type
    )
    
    db_document = crud.create_document(db, doc_data)
    
    # Generate download URL
    download_url = f"/api/v1/documents/{db_document.id}/download"
    
    return DocumentUploadResponse(
        message="File uploaded successfully",
        document=db_document,
        download_url=download_url
    )


@router.get(
    "/{document_id}",
    response_model=DocumentOut,
    summary="Get document metadata"
)
def get_document_metadata(
    document_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Retrieve document metadata by ID.
    
    - **document_id**: Document ID
    
    Returns document information (not the file itself).
    """
    document = crud.get_document(db, document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} not found"
        )
    
    return document


@router.get(
    "/{document_id}/download",
    summary="Download document file"
)
def download_document(
    document_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Download the actual document file.
    
    - **document_id**: Document ID
    
    Returns the file for download.
    """
    # Get document metadata
    document = crud.get_document(db, document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} not found"
        )
    
    # Check if file exists
    if not file_storage.file_exists(document.stored_filename):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found in storage"
        )
    
    # Return file
    file_path = file_storage.get_file_path(document.stored_filename)
    
    return FileResponse(
        path=file_path,
        filename=document.filename,
        media_type=document.file_type
    )


@router.get(
    "/",
    response_model=dict,
    summary="List all documents with pagination"
)
def list_documents(
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 10,
    document_type: Annotated[Optional[str], Query(description="Filter by type")] = None,
    db: Annotated[Session, Depends(get_db)] = None
):
    """
    List all documents with pagination.
    
    - **page**: Page number (starts at 1)
    - **page_size**: Items per page (max 100)
    - **document_type**: Optional filter by type (cv, cover_letter, etc.)
    """
    skip = (page - 1) * page_size
    documents, total = crud.get_documents(
        db,
        skip=skip,
        limit=page_size,
        document_type=document_type
    )
    
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    return {
        "documents": documents,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document"
)
def delete_document(
    document_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Delete a document and its file.
    
    - **document_id**: Document ID
    
    Removes both database record and physical file.
    """
    # Get document metadata
    document = crud.get_document(db, document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} not found"
        )
    
    # Delete physical file
    file_storage.delete_file(document.stored_filename)
    
    # Delete database record
    crud.delete_document(db, document_id)
    
    return None  # 204 No Content


@router.post(
    "/{document_id}/parse",
    response_model=ParsedCVOut,
    status_code=status.HTTP_200_OK,
    summary="Parse a CV/Resume document"
)
async def parse_document(
    document_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Parse a document (must be a CV/Resume) and extract structured data.
    
    - **document_id**: Document ID
    
    Returns structured JSON data extracted from the CV.
    """
    from app.services.ai.cv_parser_service import get_cv_parser_service
    from app.crud.parsed_cv import get_parsed_cv_by_document_id, create_parsed_cv
    from app.schemas.parsed_cv import ParsedCVCreate, ParsedCVOut
    from app.utils.file_storage import get_file_path
    
    # 1. Check if document exists
    document = crud.get_document(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} not found"
        )
        
    # 2. Check if already parsed (optional: could allow re-parsing)
    existing_parsed = get_parsed_cv_by_document_id(db, document_id)
    if existing_parsed:
        return ParsedCVOut.from_orm(existing_parsed)
        
    # 3. Get file path
    file_path = get_file_path(document.stored_filename)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical file not found"
        )
        
    # 4. Parse document
    parser_service = get_cv_parser_service()
    try:
        # Extract text
        text = parser_service.extract_text_from_file(str(file_path), document.file_type)
        
        # Parse with LLM
        parsed_data = await parser_service.parse_cv_text(text)
        
        # 5. Save to database
        # Create Pydantic model for validation/creation
        cv_create = ParsedCVCreate(
            document_id=document_id,
            raw_text=text,
            **parsed_data
        )
        
        db_parsed_cv = create_parsed_cv(db, cv_create)

        # 6. Generate and store embedding (NEW for matching)
        try:
            from app.services.ai.embeddings_service import get_embeddings_service
            from app.models.document_embedding import DocumentEmbedding

            embeddings_service = get_embeddings_service()
            
            # Construct text representation for embedding
            # We focus on skills, experience, and summary for matching
            embedding_text = f"Candidate: {parsed_data.get('name', 'Unknown')}\n"
            embedding_text += f"Skills: {', '.join(parsed_data.get('skills', []))}\n"
            
            exp_years = parsed_data.get('experience_years')
            if exp_years:
                embedding_text += f"Experience: {exp_years} years\n"
                
            summary = parsed_data.get('summary')
            if summary:
                embedding_text += f"Summary: {summary}\n"
                
            # Latest job title/company if available
            work_exp = parsed_data.get('work_experience', [])
            if work_exp and len(work_exp) > 0:
                latest = work_exp[0]
                embedding_text += f"Latest Role: {latest.get('title')} at {latest.get('company')}"

            # Generate vector
            embedding_vector = embeddings_service.embed_document(embedding_text)

            # Check if embedding exists
            existing_embedding = db.query(DocumentEmbedding).filter(
                DocumentEmbedding.document_id == document_id
            ).first()

            if existing_embedding:
                existing_embedding.embedding = embedding_vector
                existing_embedding.embedded_text = embedding_text
            else:
                doc_embedding = DocumentEmbedding(
                    document_id=document_id,
                    embedding=embedding_vector,
                    embedded_text=embedding_text
                )
                db.add(doc_embedding)
            
            db.commit()

        except Exception as e:
            # Log but don't fail the parsing if embedding fails
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to generate embedding for document {document_id}: {str(e)}")
        
        return ParsedCVOut.from_orm(db_parsed_cv)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parsing failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post(
    "/{document_id}/analyze",
    response_model=None,  # Will import CVAnalysisOut
    status_code=status.HTTP_200_OK,
    summary="Analyze CV quality and get improvement suggestions"
)
async def analyze_cv(
    document_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Analyze a parsed CV and provide quality scores and improvement suggestions.
    
    - **document_id**: Document ID
    
    Returns comprehensive CV analysis including:
    - Overall quality score (0-100)
    - Completeness, quality, and ATS scores
    - Strengths and weaknesses
    - Actionable improvement suggestions
    - Skill and experience analysis
    
    **Note**: CV must be parsed first using /documents/{id}/parse
    """
    from app.services.ai.cv_analyzer_service import get_cv_analyzer_service
    from app.crud.parsed_cv import get_parsed_cv_by_document_id
    from app.crud.cv_analysis import create_cv_analysis, get_cv_analysis_by_parsed_cv_id
    from app.schemas.cv_analysis import CVAnalysisCreate, CVAnalysisOut, Suggestion, SkillAnalysis, ExperienceAnalysis
    
    # 1. Check if document exists
    document = crud.get_document(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} not found"
        )
    
    # 2. Check if CV is parsed
    parsed_cv = get_parsed_cv_by_document_id(db, document_id)
    if not parsed_cv:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CV has not been parsed yet. Please parse the document first using /documents/{id}/parse"
        )
    
    # 3. Check if already analyzed (return cached result)
    existing_analysis = get_cv_analysis_by_parsed_cv_id(db, parsed_cv.id)
    if existing_analysis:
        return CVAnalysisOut.from_orm(existing_analysis)
    
    # 4. Analyze CV
    analyzer_service = get_cv_analyzer_service()
    try:
        analysis_result = analyzer_service.analyze_cv(parsed_cv)
        
        # 5. Convert to Pydantic models for validation
        suggestions = [Suggestion(**s) for s in analysis_result["suggestions"]]
        skill_analysis = SkillAnalysis(**analysis_result["skill_analysis"])
        experience_analysis = ExperienceAnalysis(**analysis_result["experience_analysis"])
        
        # 6. Create analysis record
        analysis_create = CVAnalysisCreate(
            parsed_cv_id=parsed_cv.id,
            overall_score=analysis_result["overall_score"],
            completeness_score=analysis_result["completeness_score"],
            quality_score=analysis_result["quality_score"],
            ats_score=analysis_result["ats_score"],
            strengths=analysis_result["strengths"],
            weaknesses=analysis_result["weaknesses"],
            suggestions=suggestions,
            skill_analysis=skill_analysis,
            experience_analysis=experience_analysis
        )
        
        db_analysis = create_cv_analysis(db, analysis_create)
        
        return CVAnalysisOut.from_orm(db_analysis)
        
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
    "/{document_id}/matching-jobs",
    response_model=JobMatchList,
    summary="Find matching jobs for a candidate"
)
def find_matching_jobs(
    document_id: int,
    limit: Annotated[int, Query(ge=1, le=50, description="Max results")] = 10,
    min_score: Annotated[float, Query(ge=0.0, le=1.0, description="Minimum match score")] = 0.5,
    db: Annotated[Session, Depends(get_db)] = None
):
    """
    Find matching jobs for a candidate CV using semantic search and rule-based scoring.
    """
    from app.services.ai.job_matcher_service import JobMatcherService
    from app.crud.parsed_cv import get_parsed_cv_by_document_id
    from app.schemas.job_match import JobMatchList

    # Check parsed cv
    parsed_cv = get_parsed_cv_by_document_id(db, document_id)
    if not parsed_cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not parsed or found."
        )

    matcher = JobMatcherService()
    matches = matcher.find_matching_jobs(db, parsed_cv.id, limit, min_score)
    
    return JobMatchList(
        document_id=document_id,
        matches=matches,
        count=len(matches)
    )


