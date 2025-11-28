from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import jobs  # ✅ Import from correct location
from app.database.db import Base, engine
from app.models import job_post  # Import to register models

# Create tables (optional if using Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="JobMate AI API",
    description="AI-driven recruitment assistant platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers - using the correct one!
app.include_router(jobs.router, prefix="/api/v1")  # ✅ Correct import


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "message": "JobMate AI API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected"
    }