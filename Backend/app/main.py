from fastapi import FastAPI
from app.database.db import Base, engine
from app.api.job_routes import router as job_router

app = FastAPI(title="JobMate API")

app.include_router(job_router)

Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "JobMate API Running"}
