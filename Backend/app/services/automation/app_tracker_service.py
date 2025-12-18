from sqlalchemy.orm import Session
from app.models.application import Application
from app.models.job_post import JobPost
from app.models.document import Document
from app.models.generated_content import CoverLetter
from typing import Optional, Dict, Any

class ApplicationTrackerService:
    def __init__(self, db: Session):
        self.db = db

    async def prepare_application_data(self, application_id: int) -> Dict[str, Any]:
        """
        Gathers all necessary data for an application to be submitted externally.
        """
        app = self.db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise ValueError("Application not found")

        # Gather related data
        job = app.job_post
        cv = app.cv_document
        
        # Look for the generated cover letter content if linked
        cl_content = ""
        if app.cover_letter_document_id:
             cl_doc = self.db.query(Document).filter(Document.id == app.cover_letter_document_id).first()
             # Logic to extract text or content could go here
             pass

        # Prepare a snapshot for automation
        data_snapshot = {
            "applicant": {
                "name": app.applicant_name,
                "email": app.applicant_email,
                "phone": app.applicant_phone
            },
            "job": {
                "title": job.title,
                "company": job.company,
                "url": app.external_url
            },
            "documents": {
                "cv_path": cv.file_path,
                "cv_name": cv.filename
            }
        }
        
        # Update the application with the snapshot
        app.application_data = data_snapshot
        app.automation_status = "pending"
        self.db.commit()
        self.db.refresh(app)
        
        return data_snapshot

    def update_automation_status(self, application_id: int, status: str):
        app = self.db.query(Application).filter(Application.id == application_id).first()
        if app:
            app.automation_status = status
            self.db.commit()
            return app
        return None
