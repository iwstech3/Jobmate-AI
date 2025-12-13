import sys
import os
import asyncio
from pathlib import Path

# Add project root to python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from sqlalchemy.orm import Session
from app.database.db import SessionLocal
from app.models.job_post import JobPost
from app.models.document import Document
from app.models.parsed_cv import ParsedCV
from app.models.document_embedding import DocumentEmbedding
from app.models.job_embedding import JobEmbedding
from app.models.job_analysis import JobAnalysis

from app.services.ai.embeddings_service import get_embeddings_service

def seed_data():
    db = SessionLocal()
    embeddings_service = get_embeddings_service()
    
    print("--- Seeding Data for Matching Agent ---")

    # 1. Create a Sample Job Post
    print("\n1. Creating Sample Job Post...")
    job_post = JobPost(
        title="Senior Python Backend Engineer",
        company="AI Future Corp",
        location="Remote",
        job_type="Full-time",
        description="We are looking for a Senior Python Developer with FastAPI and AI experience. Must know PostgreSQL and Vector databases."
    )
    db.add(job_post)
    db.commit()
    db.refresh(job_post)
    print(f"   Created Job: {job_post.title} (ID: {job_post.id})")

    # 1.1 Create Job Analysis (Mocked to save time/cost, or could use AnalyzerService)
    # We'll just create it manually for speed and reliability here.
    analysis = JobAnalysis(
        job_post_id=job_post.id,
        required_skills=["Python", "FastAPI", "PostgreSQL", "AI", "Vector Databases"],
        preferred_skills=["Docker", "AWS"],
        experience_level="Senior",
        min_years_experience=5,
        max_years_experience=10,
        education_requirements=["Bachelor's Degree"],
        certifications=[],
        responsibilities=["Build AI agents", "Optimize backend performance"],
        benefits=["Remote work", "Competitive salary"],
        key_technologies=["Python", "FastAPI", "PostgreSQL"],
        soft_skills=["Communication", "Leadership"],
        employment_type="full-time",
        remote_policy="remote"
    )
    db.add(analysis)
    
    # 1.2 Create Job Embedding
    embedding_text = f"{job_post.title}\nCompany: {job_post.company}\nRequired skills: Python, FastAPI, PostgreSQL, AI\nResponsibilities: Build AI agents"
    print("   Generating Job Embedding...")
    job_vector = embeddings_service.embed_document(embedding_text)
    
    job_embedding = JobEmbedding(
        job_post_id=job_post.id,
        embedding=job_vector,
        embedded_text=embedding_text
    )
    db.add(job_embedding)
    db.commit()
    print("   Job Data Seeded Successfully.")

    # 2. Create a Sample Candidate (Parsed CV)
    print("\n2. Creating Sample Candidate...")
    
    # 2.1 Create Document Stub
    doc = Document(
        filename="john_doe_cv.pdf",
        stored_filename="mock_john_doe_cv.pdf",
        file_path="/tmp/mock_john_doe_cv.pdf",
        file_type="application/pdf",
        file_size=1024
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    # 2.2 Create Parsed CV
    parsed_cv = ParsedCV(
        document_id=doc.id,
        name="John Doe",
        email="john@example.com",
        phone="123-456-7890",
        skills=["Python", "Django", "FastAPI", "PostgreSQL", "Machine Learning"],
        experience_years=6,
        summary="Experienced Python Developer with a focus on web frameworks and AI integration.",
        education=[{"degree": "BS Computer Science", "institution": "Tech University", "year": "2018"}],
        work_experience=[
            {"title": "Backend Developer", "company": "Startup Inc", "duration": "2019-2024", "description": "Built APIs"}
        ]
    )
    db.add(parsed_cv)
    db.commit()
    print(f"   Created Candidate: {parsed_cv.name} (ID: {parsed_cv.id})")
    
    # 2.3 Create Candidate Embedding
    print("   Generating Candidate Embedding...")
    cv_text = f"Candidate: {parsed_cv.name}\nSkills: Python, Django, FastAPI, PostgreSQL, Machine Learning\nExperience: 6 years\nSummary: {parsed_cv.summary}"
    cv_vector = embeddings_service.embed_document(cv_text)
    
    doc_embedding = DocumentEmbedding(
        document_id=doc.id,
        embedding=cv_vector,
        embedded_text=cv_text
    )
    db.add(doc_embedding)
    db.commit()
    print("   Candidate Data Seeded Successfully.")
    
    print("\n--- Seeding Complete ---")
    print(f"Job ID: {job_post.id}")
    print(f"Document ID: {doc.id}")
    print("\nNow run 'python scripts/test_job_matching.py' to see the match!")

if __name__ == "__main__":
    seed_data()
