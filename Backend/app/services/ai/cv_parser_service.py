import json
import logging
import traceback
from typing import Dict, Any, Optional
from pathlib import Path

# Extractors
import pdfplumber
import docx
import PyPDF2

from app.services.ai.llm_service import get_llm_service

logger = logging.getLogger(__name__)

class CVParserService:
    def __init__(self):
        self.llm_service = get_llm_service()

    def extract_text_from_file(self, file_path: str, file_type: str) -> str:
        """
        Extract text from file based on extension/type.
        """
        # Feature: Fix File Path Handling (absolute/relative check)
        path = Path(file_path)
        if not path.is_absolute():
            path = Path.cwd() / file_path
            
        if not path.exists():
            logger.error(f"File not found at path: {path}")
            raise FileNotFoundError(f"File not found at {path}")

        extension = path.suffix.lower()
        
        try:
            logger.info(f"Extracting text from {path} (type: {extension})")
            if extension == ".pdf":
                return self._extract_from_pdf(path)
            elif extension in [".docx", ".doc"]:
                return self._extract_from_docx(path)
            elif extension == ".txt":
                return path.read_text(encoding="utf-8", errors="ignore")
            else:
                raise ValueError(f"Unsupported file extension: {extension}")
        except Exception as e:
            logger.error(f"Text extraction failed for {path}: {str(e)}")
            logger.error(traceback.format_exc())
            raise ValueError(f"Could not extract text: {str(e)}")

    def _extract_from_pdf(self, path: Path) -> str:
        text = ""
        try:
            # Try pdfplumber first (better extraction)
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
        except Exception:
            # Fallback to PyPDF2
            logger.warning("pdfplumber failed, falling back to PyPDF2")
            try:
                reader = PyPDF2.PdfReader(str(path))
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            except Exception as e:
                raise ValueError(f"PDF extraction failed: {e}")
                
        return text

    def _extract_from_docx(self, path: Path) -> str:
        try:
            doc = docx.Document(path)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
             # Try simple text read for older .doc or mismatch
            logger.warning(f"python-docx failed: {e}, attempting raw read")
            try:
                with open(path, "rb") as f:
                    return f.read().decode("utf-8", errors="ignore")
            except Exception:
                raise ValueError(f"DOCX extraction failed: {e}")

    def clean_json_response(self, text: str) -> str:
        """Remove markdown code fences from JSON response"""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]  # Remove ```json
        elif text.startswith("```"):
            text = text[3:]   # Remove ```
        if text.endswith("```"):
            text = text[:-3]  # Remove trailing ```
        return text.strip()

    async def parse_cv_text(self, text: str) -> Dict[str, Any]:
        """
        Send text to LLM and parse into structured JSON.
        """
        try:
            logger.info("Starting CV parsing with LLM")
            if not text.strip():
                raise ValueError("Extracted text is empty")

            system_message = "You are a CV parsing expert. Extract structured information from resumes."
            
            prompt = f"""
            Extract the following information from this CV and return ONLY valid JSON:
            
            {{
                "name": "full name",
                "email": "email or null",
                "phone": "phone or null",
                "skills": ["skill1", "skill2"],
                "experience_years": number or null,
                "education": [{{"degree": "", "institution": "", "year": ""}}],
                "work_experience": [{{"title": "", "company": "", "duration": "", "description": ""}}],
                "certifications": ["cert1"] or null,
                "summary": "2-3 sentence professional summary"
            }}
            
            If a field is not found, use null or empty list.
            
            CV Text:
            {text[:20000]}  # Truncate if too long to avoid token limits
            """

            response = self.llm_service.generate_structured(prompt, output_format="json")
            
            # Simple validation/cleaning
            if isinstance(response, str):
                 cleaned_res = self.clean_json_response(response)
                 try:
                     parsed_data = json.loads(cleaned_res)
                     return parsed_data
                 except json.JSONDecodeError as e:
                     logger.error(f"JSON decode failed: {e}. Content: {cleaned_res[:100]}...")
                     # Graceful Fallback as requested
                     logger.warning("Returning partial/fallback data due to JSON error")
                     return {
                        "name": "Unknown",
                        "email": None,
                        "phone": None,
                        "skills": [],
                        "experience_years": None,
                        "education": [],
                        "work_experience": [],
                        "certifications": [],
                        "summary": text[:200] + "..." # Fallback summary
                    }
            
            return response
            
        except Exception as e:
            logger.error(f"LLM parsing failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise ValueError(f"Parsing failed due to LLM error: {str(e)}")

# Singleton instance
cv_parser_service = CVParserService()

def get_cv_parser_service() -> CVParserService:
    return cv_parser_service
