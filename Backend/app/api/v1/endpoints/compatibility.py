from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated, List

from app.database.db import get_db
from app.services.ai.compatibility_scorer_service import get_compatibility_scorer_service, CompatibilityScorerService
from app.schemas.compatibility import CompatibilityScore, CompatibilityRequest, BatchCompatibilityRequest
from app.crud.parsed_cv import get_parsed_cv
from app.crud.job_post import get_job_post
from app.crud.job_analysis import get_job_analysis_by_job_id
from app.models.document_embedding import DocumentEmbedding
from app.models.job_embedding import JobEmbedding
from app.services.ai.embeddings_service import get_embeddings_service

router = APIRouter(prefix="/compatibility", tags=["Compatibility"])

def get_scorer_service() -> CompatibilityScorerService:
    return get_compatibility_scorer_service()

@router.post(
    "/score",
    response_model=CompatibilityScore,
    summary="Calculate compatibility score for CV and Job"
)
def calculate_compatibility_score(
    request: CompatibilityRequest,
    db: Annotated[Session, Depends(get_db)],
    scorer: Annotated[CompatibilityScorerService, Depends(get_scorer_service)]
):
    """
    Calculate detailed compatibility score for a specific parsed CV and Job Post.
    """
    # 1. Fetch Data
    parsed_cv = get_parsed_cv(db, request.parsed_cv_id)
    if not parsed_cv:
        raise HTTPException(status_code=404, detail="Parsed CV not found")
        
    job_post = get_job_post(db, request.job_post_id)
    if not job_post:
        raise HTTPException(status_code=404, detail="Job Post not found")
        
    job_analysis = get_job_analysis_by_job_id(db, request.job_post_id)
    if not job_analysis:
        raise HTTPException(status_code=404, detail="Job Analysis not found. Please analyze the job first.")
        
    # 2. Calculate Semantic Similarity (if embeddings exist)
    # We can fetch embeddings and calculate cosine similarity
    doc_embedding = db.query(DocumentEmbedding).filter(DocumentEmbedding.document_id == parsed_cv.document_id).first()
    job_embedding = db.query(JobEmbedding).filter(JobEmbedding.job_post_id == job_post.id).first()
    
    similarity = 0.5 # Default neutral
    if doc_embedding and job_embedding:
        import numpy as np
        # Convert python lists to numpy arrays if needed, or assume they are lists
        # pgvector usually returns lists or numpy arrays depending on driver
        # Simply use cosine similarity formula
        
        # Note: In a real prod environment, we might let the DB do this or use helper functions
        # For now, simple dot product if normalized, or full cosine
        
        # Scikit-learn or numpy is robust.
        # Assuming normalized vectors from Gemini
        vec_a = doc_embedding.embedding
        vec_b = job_embedding.embedding
        
        # Ensure list/array
        if isinstance(vec_a, str): vec_a = [float(x) for x in vec_a.strip('[]').split(',')]
        if isinstance(vec_b, str): vec_b = [float(x) for x in vec_b.strip('[]').split(',')]
        
        dot_product = sum(a*b for a,b in zip(vec_a, vec_b))
        norm_a = sum(a*a for a in vec_a) ** 0.5
        norm_b = sum(b*b for b in vec_b) ** 0.5
        
        if norm_a > 0 and norm_b > 0:
            similarity = dot_product / (norm_a * norm_b)
            
    # 3. Calculate Compatibility
    score = scorer.calculate_compatibility(
        parsed_cv=parsed_cv,
        job_analysis=job_analysis,
        job_post=job_post,
        semantic_similarity=float(similarity)
    )
    
    return score

@router.get(
    "/cv/{parsed_cv_id}/job/{job_post_id}",
    response_model=CompatibilityScore,
    summary="Get compatibility score (GET)"
)
def get_compatibility_score(
    parsed_cv_id: int,
    job_post_id: int,
    db: Annotated[Session, Depends(get_db)],
    scorer: Annotated[CompatibilityScorerService, Depends(get_scorer_service)]
):
    request = CompatibilityRequest(parsed_cv_id=parsed_cv_id, job_post_id=job_post_id)
    return calculate_compatibility_score(request, db, scorer)

@router.post(
    "/batch",
    response_model=List[CompatibilityScore],
    summary="Batch calculate scores for one CV against multiple Jobs"
)
def batch_compatibility_score(
    request: BatchCompatibilityRequest,
    db: Annotated[Session, Depends(get_db)],
    scorer: Annotated[CompatibilityScorerService, Depends(get_scorer_service)]
):
    results = []
    
    # Pre-fetch CV once
    parsed_cv = get_parsed_cv(db, request.parsed_cv_id)
    if not parsed_cv:
        raise HTTPException(status_code=404, detail="Parsed CV not found")
        
    doc_embedding = db.query(DocumentEmbedding).filter(DocumentEmbedding.document_id == parsed_cv.document_id).first()
    vec_a = None
    if doc_embedding:
         # Parse once
         vec_a = doc_embedding.embedding
         if isinstance(vec_a, str): vec_a = [float(x) for x in vec_a.strip('[]').split(',')]

    for job_id in request.job_post_ids:
        try:
            job_post = get_job_post(db, job_id)
            if not job_post: continue
            
            job_analysis = get_job_analysis_by_job_id(db, job_id)
            if not job_analysis: continue
            
            # Semantic Sim
            similarity = 0.5
            if vec_a:
                job_embedding = db.query(JobEmbedding).filter(JobEmbedding.job_post_id == job_id).first()
                if job_embedding:
                     vec_b = job_embedding.embedding
                     if isinstance(vec_b, str): vec_b = [float(x) for x in vec_b.strip('[]').split(',')]
                     
                     dot = sum(a*b for a,b in zip(vec_a, vec_b))
                     norm_a = sum(a*a for a in vec_a) ** 0.5
                     norm_b = sum(b*b for b in vec_b) ** 0.5
                     if norm_a > 0 and norm_b > 0:
                        similarity = dot / (norm_a * norm_b)
            
            score = scorer.calculate_compatibility(
                parsed_cv=parsed_cv,
                job_analysis=job_analysis,
                job_post=job_post,
                semantic_similarity=float(similarity)
            )
            results.append(score)
            
        except Exception as e:
            # Skip failed items in batch
            import logging
            logging.getLogger(__name__).error(f"Batch scoring failed for job {job_id}: {e}")
            continue
            
    return results
