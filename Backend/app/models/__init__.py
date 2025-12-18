# Core Models
from app.models.job_post import JobPost
from app.models.document import Document
from app.models.application import Application
from app.models.saved_job import SavedJob
from app.models.job_view import JobView
from app.models.job_status_history import JobStatusHistory

# AI & Analysis Models
from app.models.job_embedding import JobEmbedding
from app.models.document_embedding import DocumentEmbedding
from app.models.parsed_cv import ParsedCV
from app.models.cv_analysis import CVAnalysis
from app.models.job_analysis import JobAnalysis
from app.models.generated_content import CoverLetter

__all__ = [
    "JobPost",
    "Document",
    "Application",
    "SavedJob",
    "JobView",
    "JobStatusHistory",
    "JobEmbedding",
    "DocumentEmbedding",
    "ParsedCV",
    "CVAnalysis",
    "JobAnalysis",
    "CoverLetter"
]
