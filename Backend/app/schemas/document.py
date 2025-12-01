from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DocumentBase(BaseModel):
    """Base schema for documents"""
    filename: str
    file_type: str
    file_size: int
    document_type: Optional[str] = None


class DocumentCreate(DocumentBase):
    """Schema for creating a document record"""
    stored_filename: str
    file_path: str


class DocumentOut(DocumentBase):
    """Schema for document responses"""
    id: int
    stored_filename: str
    file_path: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    """Schema for upload response"""
    message: str
    document: DocumentOut
    download_url: str = Field(..., description="URL to download the file")