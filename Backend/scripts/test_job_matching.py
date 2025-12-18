import sys
import os
from pathlib import Path

# Add project root to python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from sqlalchemy.orm import Session
from app.database.db import SessionLocal
from app.services.ai.job_matcher_service import JobMatcherService
from app.models.parsed_cv import ParsedCV
from app.models.job_post import JobPost
from app.models.job_embedding import JobEmbedding
from app.models.document_embedding import DocumentEmbedding

def test_matching():
    db = SessionLocal()
    matcher = JobMatcherService()
    
    print("--- Testing Semantic Job Matching ---")
    
    # 1. Test Job Matching for Candidate
    print("\n1. Testing Job Matching for Candidate...")
    
    # Find a candidate with embedding
    candidate = db.query(ParsedCV).join(DocumentEmbedding, ParsedCV.document_id == DocumentEmbedding.document_id).first()
    
    if candidate:
        print(f"Found candidate: {candidate.name} (ID: {candidate.id})")
        parsed_cv_id = candidate.id
        
        matches = matcher.find_matching_jobs(db, parsed_cv_id, limit=5)
        
        if matches:
            print(f"Found {len(matches)} matching jobs:")
            for m in matches:
                print(f"  - [{m['match_percentage']}%] {m['job_title']} at {m['company']}")
                print(f"    Reason: {m['match_explanation']}")
        else:
            print("No matches found. Ensure you have job posts with embeddings.")
    else:
        print("No candidate with embedding found. Upload and parse a CV, then run analysis.")

    # 2. Test Candidate Matching for Job
    print("\n2. Testing Candidate Matching for Job...")
    
    # Find a job with embedding
    job = db.query(JobPost).join(JobEmbedding, JobPost.id == JobEmbedding.job_post_id).first()
    
    if job:
        print(f"Found job: {job.title} (ID: {job.id})")
        job_id = job.id
        
        matches = matcher.find_matching_candidates(db, job_id, limit=5)
        
        if matches:
            print(f"Found {len(matches)} matching candidates:")
            for m in matches:
                print(f"  - [{m['match_percentage']}%] {m['name']}")
                print(f"    Reason: {m['match_explanation']}")
        else:
            print("No matches found. Ensure you have candidates with embeddings.")
    else:
        print("No job with embedding found. Create and analyze a job post.")

if __name__ == "__main__":
    test_matching()
