from sqlalchemy import Column, Integer, String, DateTime, BigInteger, func
from app.database.db import Base


class Document(Base):
    """
    Model for storing uploaded document metadata.
    Actual files are stored in /storage directory.
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, comment="Original filename")
    stored_filename = Column(String(255), nullable=False, unique=True, comment="Unique filename in storage")
    file_path = Column(String(500), nullable=False, comment="Full path to file")
    file_type = Column(String(255), nullable=False, comment="MIME type (e.g., application/pdf)")
    file_size = Column(BigInteger, nullable=False, comment="File size in bytes")
    
    # Optional: Link to user when you implement authentication
    # user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Optional: Document category
    document_type = Column(
        String(50), 
        nullable=True, 
        comment="Type: cv, cover_letter, certificate, etc."
    )
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', type='{self.document_type}')>"