"""Debug CV Parser"""
import sys
sys.path.insert(0, '.')

from app.database.db import SessionLocal
from app.models.document import Document
from app.services.ai.cv_parser_service import CVParserService

db = SessionLocal()

try:
    # Get document
    doc = db.query(Document).filter(Document.id == 1).first()
    if not doc:
        print("[X] Document 1 not found")
        sys.exit(1)
    
    print(f"[OK] Document found: {doc.filename}")
    print(f"   File path: {doc.file_path}")
    print(f"   File type: {doc.file_type}")
    
    import asyncio
    
    # 1. Extract Text
    print("[?] Extracting text...")
    parser = CVParserService()
    text = parser.extract_text_from_file(doc.file_path, doc.file_type)
    print(f"[OK] Text extracted ({len(text)} chars)")
    
    # 2. Parse Text (Async)
    print("[?] Parsing with LLM...")
    result = asyncio.run(parser.parse_cv_text(text))
    
    print("[OK] Parsing successful!")
    
    print(f"   Name: {result.get('name')}")
    print(f"   Skills: {len(result.get('skills', []))} found")
    
except Exception as e:
    print(f"\n[X] Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()