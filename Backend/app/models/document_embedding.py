from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database.db import Base


class DocumentEmbedding(Base):
    """Store vector embeddings for documents (CVs)"""
    __tablename__ = "document_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), unique=True, nullable=False)
    embedding = Column(Vector(768), nullable=False)
    embedded_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    document = relationship("Document", backref="embedding")