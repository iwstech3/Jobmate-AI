from sqlalchemy.orm import Session
from app.models.parsed_cv import ParsedCV
from app.schemas.parsed_cv import ParsedCVCreate

def create_parsed_cv(db: Session, parsed_cv: ParsedCVCreate) -> ParsedCV:
    db_parsed_cv = ParsedCV(
        document_id=parsed_cv.document_id,
        name=parsed_cv.name,
        email=parsed_cv.email,
        phone=parsed_cv.phone,
        skills=parsed_cv.skills,
        experience_years=parsed_cv.experience_years,
        education=[e.model_dump() for e in parsed_cv.education] if parsed_cv.education else None,
        work_experience=[w.model_dump() for w in parsed_cv.work_experience] if parsed_cv.work_experience else None,
        certifications=parsed_cv.certifications,
        summary=parsed_cv.summary,
        raw_text=parsed_cv.raw_text
    )
    db.add(db_parsed_cv)
    db.commit()
    db.refresh(db_parsed_cv)
    return db_parsed_cv

def get_parsed_cv(db: Session, parsed_cv_id: int) -> ParsedCV:
    return db.query(ParsedCV).filter(ParsedCV.id == parsed_cv_id).first()

def get_parsed_cv_by_document_id(db: Session, document_id: int) -> ParsedCV:
    return db.query(ParsedCV).filter(ParsedCV.document_id == document_id).first()
