import logging
from typing import Optional, Dict, Any
from app.services.ai.llm_service import get_llm_service
from app.models.job_post import JobPost
from app.models.parsed_cv import ParsedCV

logger = logging.getLogger(__name__)

class GeneratorService:
    """
    Service for generating tailored recruitment content (cover letters, optimized CV sections).
    """
    
    def __init__(self):
        self.llm = get_llm_service()

    async def generate_cover_letter(
        self, 
        cv_text: str, 
        job: JobPost, 
        custom_instructions: Optional[str] = None
    ) -> str:
        """
        Generate a professional cover letter tailored to a specific job description.
        """
        system_message = (
            "You are an expert career coach and professional resume writer. "
            "Your goal is to write a highly persuasive, professional, and tailored cover letter. "
            "STRICT RULES:\n"
            "1. Use ONLY facts provided in the candidate's CV.\n"
            "2. DO NOT invent experiences, skills, or certifications.\n"
            "3. Align the candidate's strengths with the job's key requirements.\n"
            "4. Use a professional, confident, yet humble tone.\n"
            "5. The output should be in Markdown format."
        )
        
        prompt = f"""
        JOB TITLE: {job.title}
        COMPANY: {job.company}
        JOB DESCRIPTION: {job.description}
        
        CANDIDATE CV TEXT:
        {cv_text}
        
        ADDITIONAL USER INSTRUCTIONS:
        {custom_instructions or "None provided."}
        
        Please generate a tailored cover letter for this position.
        """
        
        try:
            response = self.llm.generate(prompt=prompt, system_message=system_message)
            return response
        except Exception as e:
            logger.error(f"Error generating cover letter: {str(e)}")
            raise Exception(f"Failed to generate cover letter: {str(e)}")

    async def tailor_cv_summary(
        self, 
        cv_text: str, 
        job_description: str
    ) -> str:
        """
        Generate an optimized "Professional Summary" for a CV based on a job post.
        """
        system_message = (
            "You are a professional CV optimizer. Rewrite the candidate's professional summary "
            "to better align with the provided job description while remaining 100% factual."
        )
        
        prompt = f"""
        JOB DESCRIPTION:
        {job_description}
        
        CANDIDATE CV:
        {cv_text}
        
        Generate a 3-4 sentence professional summary that highlights relevant skills for this specific job.
        """
        
        return self.llm.generate(prompt=prompt, system_message=system_message)

def get_generator_service() -> GeneratorService:
    return GeneratorService()
