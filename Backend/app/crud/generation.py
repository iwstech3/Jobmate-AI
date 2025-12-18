from sqlalchemy.orm import Session
from app.models.generated_content import CoverLetter
from app.schemas.generation import CoverLetterGenerateRequest

def create_cover_letter(db: Session, cover_letter_data: dict) -> CoverLetter:
    db_cover_letter = CoverLetter(**cover_letter_data)
    db.add(db_cover_letter)
    db.commit()
    db.refresh(db_cover_letter)
    return db_cover_letter

def get_cover_letter(db: Session, cover_letter_id: int) -> CoverLetter:
    return db.query(CoverLetter).filter(CoverLetter.id == cover_letter_id).first()

def get_cover_letters_by_cv(db: Session, cv_id: int) -> list[CoverLetter]:
    return db.query(CoverLetter).filter(CoverLetter.parsed_cv_id == cv_id).all()

def get_cover_letters(db: Session, skip: int = 0, limit: int = 100) -> list[CoverLetter]:
    return db.query(CoverLetter).offset(skip).limit(limit).all()
