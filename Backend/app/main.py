from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import jobs, documents  # ← Add documents
from app.database.db import Base, engine
from app.models import job_post, document  # ← Add document

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")  # ← Add this line


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