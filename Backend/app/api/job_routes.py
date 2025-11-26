from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.db import SessionLocal
from app.models.job_post import JobPost
from app.schemas.job_post import JobPostCreate, JobPostOut

router = APIRouter(prefix="/jobs", tags=["Jobs"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=JobPostOut)
def create_job(job: JobPostCreate, db: Session = Depends(get_db)):
    new_job = JobPost(**job.dict())
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job

@router.get("/", response_model=list[JobPostOut])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(JobPost).all()

@router.get("/search")
def search_jobs(q: str, db: Session = Depends(get_db)):
    return db.query(JobPost).filter(JobPost.title.ilike(f"%{q}%")).all()
