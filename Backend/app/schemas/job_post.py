from pydantic import BaseModel

class JobPostCreate(BaseModel):
    title: str
    company: str
    location: str | None = None
    job_type: str | None = None
    description: str

class JobPostOut(JobPostCreate):
    id: int

    class Config:
        orm_mode = True
