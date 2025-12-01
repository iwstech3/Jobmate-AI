from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.document import Document
from app.schemas.document import DocumentCreate


def create_document(db: Session, doc_data: DocumentCreate) -> Document:
    """
    Create a new document record in the database.
    
    Args:
        db: Database session
        doc_data: Document data
        
    Returns:
        Created Document instance
    """
    db_document = Document(**doc_data.model_dump())
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


def get_document(db: Session, document_id: int) -> Optional[Document]:
    """
    Retrieve a document by ID.
    
    Args:
        db: Database session
        document_id: Document ID
        
    Returns:
        Document if found, None otherwise
    """
    return db.query(Document).filter(Document.id == document_id).first()


def get_document_by_stored_filename(db: Session, stored_filename: str) -> Optional[Document]:
    """
    Retrieve a document by its stored filename.
    
    Args:
        db: Database session
        stored_filename: Unique stored filename
        
    Returns:
        Document if found, None otherwise
    """
    return db.query(Document).filter(Document.stored_filename == stored_filename).first()


def get_documents(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    document_type: Optional[str] = None
) -> tuple[List[Document], int]:
    """
    Retrieve documents with pagination and optional filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        document_type: Filter by document type (cv, cover_letter, etc.)
        
    Returns:
        Tuple of (list of Documents, total count)
    """
    query = db.query(Document)
    
    if document_type:
        query = query.filter(Document.document_type == document_type)
    
    total = query.count()
    documents = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    
    return documents, total


def delete_document(db: Session, document_id: int) -> bool:
    """
    Delete a document record from database.
    Note: This does NOT delete the actual file from storage.
    Use file_storage.delete_file() for that.
    
    Args:
        db: Database session
        document_id: Document ID
        
    Returns:
        True if deleted, False if not found
    """
    db_document = get_document(db, document_id)
    
    if not db_document:
        return False
    
    db.delete(db_document)
    db.commit()
    return True


def update_document_type(
    db: Session,
    document_id: int,
    document_type: str
) -> Optional[Document]:
    """
    Update document type.
    
    Args:
        db: Database session
        document_id: Document ID
        document_type: New document type
        
    Returns:
        Updated Document if found, None otherwise
    """
    db_document = get_document(db, document_id)
    
    if not db_document:
        return None
    
    db_document.document_type = document_type
    db.commit()
    db.refresh(db_document)
    return db_document