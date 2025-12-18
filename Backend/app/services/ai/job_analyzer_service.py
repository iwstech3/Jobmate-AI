"""
Job Analyzer Service
Extracts structured requirements and metadata from job descriptions using Gemini LLM
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional
from app.services.ai.llm_service import get_llm_service
from app.models.job_post import JobPost

logger = logging.getLogger(__name__)


class JobAnalyzerService:
    """
    Job Analyzer Service - extracts structured data from job descriptions.
    Uses Gemini LLM for intelligent parsing and categorization.
    """
    
    def __init__(self):
        """Initialize Job Analyzer with LLM service"""
        self.llm_service = get_llm_service()
        
    def analyze_job(self, job_post: JobPost) -> Dict[str, Any]:
        """
        Analyze a job posting and extract structured requirements.
        
        Args:
            job_post: JobPost model instance
            
        Returns:
            Dictionary with extracted job requirements and metadata
        """
        logger.info(f"Starting job analysis for JobPost ID: {job_post.id}")
        
        try:
            # 1. Analyze with LLM for comprehensive extraction
            analysis = self._analyze_with_llm(job_post)
            
            # 2. Validate and clean data
            analysis = self._validate_and_clean(analysis)
            
            # 3. Enhance with rule-based extraction (fallback/supplement)
            analysis = self._enhance_with_rules(job_post, analysis)
            
            # 4. Prepare embedding text (NEW)
            embedding_text = self._prepare_embedding_text(job_post, analysis)
            
            logger.info(f"Job analysis completed. Experience level: {analysis.get('experience_level')}")
            
            # Return both analysis and embedding_text
            return {
                "analysis": analysis,
                "embedding_text": embedding_text
            }
            
        except Exception as e:
            logger.error(f"Error during job analysis: {str(e)}", exc_info=True)
            # Fallback to rule-based analysis
            fallback_analysis = self._fallback_analysis(job_post)
            embedding_text = self._prepare_embedding_text(job_post, fallback_analysis)
            return {
                "analysis": fallback_analysis,
                "embedding_text": embedding_text
            }
    
    def _analyze_with_llm(self, job_post: JobPost) -> Dict[str, Any]:
        """
        Use Gemini LLM to extract structured data from job description.
        
        Args:
            job_post: JobPost model instance
            
        Returns:
            Dictionary with extracted job data
        """
        try:
            system_message = "You are an expert HR analyst and recruiter specializing in extracting structured data from job descriptions. Be thorough but accurate."
            
            prompt = f"""Analyze this job posting and extract all relevant information. Return ONLY valid JSON with no markdown formatting.

Job Title: {job_post.title}
Company: {job_post.company}
Location: {job_post.location}
Job Type: {job_post.job_type}

Description:
{job_post.description}

Extract and categorize the following information. Only include information explicitly stated or strongly implied:

{{
  "required_skills": [<list of must-have technical skills>],
  "preferred_skills": [<list of nice-to-have skills>],
  "experience_level": "<entry|junior|mid|senior|lead|principal>",
  "min_years_experience": <number or null>,
  "max_years_experience": <number or null>,
  "education_requirements": [<list of education requirements>],
  "certifications": [<list of certifications mentioned>],
  "responsibilities": [<list of 5-8 key responsibilities>],
  "benefits": [<list of benefits/perks mentioned>],
  "salary_range": {{
    "min": <number or null>,
    "max": <number or null>,
    "currency": "<USD|EUR|GBP|etc or null>",
    "period": "<annual|monthly|hourly or null>"
  }},
  "employment_type": "<full-time|part-time|contract|internship>",
  "remote_policy": "<on-site|hybrid|fully-remote|flexible or null>",
  "industry": "<Technology|Finance|Healthcare|etc or null>",
  "company_size": "<startup|small|medium|large|enterprise or null>",
  "key_technologies": [<top 5-10 technologies/tools mentioned>],
  "soft_skills": [<communication, leadership, teamwork, etc>]
}}

Guidelines:
- Separate required vs preferred skills carefully
- For experience_level, use keywords: entry (0-1yr), junior (1-3yr), mid (3-5yr), senior (5-8yr), lead (8-12yr), principal (12+yr)
- Extract salary only if explicitly mentioned
- List responsibilities as action-oriented statements
- Include only benefits explicitly mentioned
- Deduplicate similar skills (e.g., "Python" and "Python 3" → "Python")
"""

            response = self.llm_service.generate_structured(prompt, system_message=system_message, output_format="json")
            
            # Clean and parse JSON
            cleaned_response = self._clean_json_response(response)
            parsed_response = json.loads(cleaned_response)
            
            logger.info("LLM analysis successful")
            return parsed_response
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}. Response: {response[:200]}")
            # Retry with simpler prompt
            return self._simple_llm_analysis(job_post)
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}", exc_info=True)
            return self._default_response()
    
    def _simple_llm_analysis(self, job_post: JobPost) -> Dict[str, Any]:
        """Simplified LLM analysis as fallback"""
        try:
            prompt = f"""Extract key information from this job posting. Return JSON only.

Title: {job_post.title}
Description: {job_post.description[:1000]}

Return:
{{
  "required_skills": [<list of skills>],
  "experience_level": "mid",
  "responsibilities": [<3-5 responsibilities>],
  "employment_type": "full-time"
}}"""
            
            response = self.llm_service.generate_structured(prompt, output_format="json")
            cleaned = self._clean_json_response(response)
            result = json.loads(cleaned)
            
            # Add defaults for missing fields
            return self._add_default_fields(result)
        except:
            return self._default_response()
    
    def _clean_json_response(self, text: str) -> str:
        """Remove markdown code fences from JSON response"""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
    
    def _validate_and_clean(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean extracted data.
        
        Args:
            analysis: Raw analysis from LLM
            
        Returns:
            Cleaned and validated analysis
        """
        # Ensure arrays are not null
        array_fields = [
            "required_skills", "preferred_skills", "education_requirements",
            "certifications", "responsibilities", "benefits",
            "key_technologies", "soft_skills"
        ]
        for field in array_fields:
            if field not in analysis or analysis[field] is None:
                analysis[field] = []
        
        # Validate experience level
        valid_levels = ["entry", "junior", "mid", "senior", "lead", "principal"]
        if "experience_level" not in analysis or analysis["experience_level"] not in valid_levels:
            analysis["experience_level"] = self._detect_experience_level(analysis)
        
        # Validate employment type
        valid_types = ["full-time", "part-time", "contract", "internship"]
        if "employment_type" not in analysis or analysis["employment_type"] not in valid_types:
            analysis["employment_type"] = "full-time"  # Default
        
        # Deduplicate skills
        analysis["required_skills"] = self._deduplicate_skills(analysis["required_skills"])
        analysis["preferred_skills"] = self._deduplicate_skills(analysis["preferred_skills"])
        analysis["key_technologies"] = self._deduplicate_skills(analysis["key_technologies"])
        
        # Ensure at least some required skills
        if not analysis["required_skills"] and analysis["key_technologies"]:
            analysis["required_skills"] = analysis["key_technologies"][:5]
        
        return analysis
    
    def _detect_experience_level(self, analysis: Dict[str, Any]) -> str:
        """Detect experience level from years or other indicators"""
        min_years = analysis.get("min_years_experience", 0) or 0
        max_years = analysis.get("max_years_experience", 0) or 0
        avg_years = (min_years + max_years) / 2 if max_years > 0 else min_years
        
        if avg_years <= 1:
            return "entry"
        elif avg_years <= 3:
            return "junior"
        elif avg_years <= 5:
            return "mid"
        elif avg_years <= 8:
            return "senior"
        elif avg_years <= 12:
            return "lead"
        else:
            return "principal"
    
    def _deduplicate_skills(self, skills: List[str]) -> List[str]:
        """Remove duplicate and very similar skills"""
        if not skills:
            return []
        
        # Convert to lowercase for comparison
        seen = set()
        unique_skills = []
        
        for skill in skills:
            skill_lower = skill.lower().strip()
            # Simple deduplication - could be enhanced
            if skill_lower not in seen:
                seen.add(skill_lower)
                unique_skills.append(skill.strip())
        
        return unique_skills
    
    def _enhance_with_rules(self, job_post: JobPost, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance LLM analysis with rule-based extraction.
        
        Args:
            job_post: JobPost model instance
            analysis: Analysis from LLM
            
        Returns:
            Enhanced analysis
        """
        description = job_post.description.lower()
        
        # Detect remote policy if not found
        if not analysis.get("remote_policy"):
            if any(keyword in description for keyword in ["fully remote", "100% remote", "remote-first"]):
                analysis["remote_policy"] = "fully-remote"
            elif any(keyword in description for keyword in ["hybrid", "flexible"]):
                analysis["remote_policy"] = "hybrid"
            elif "on-site" in description or "office" in description:
                analysis["remote_policy"] = "on-site"
        
        # Extract years of experience if missing
        if not analysis.get("min_years_experience"):
            years_match = re.search(r'(\d+)\+?\s*years?', description)
            if years_match:
                analysis["min_years_experience"] = int(years_match.group(1))
        
        # Detect common technologies if key_technologies is empty
        if not analysis.get("key_technologies"):
            common_tech = [
                "Python", "Java", "JavaScript", "TypeScript", "React", "Node.js",
                "Docker", "Kubernetes", "AWS", "Azure", "PostgreSQL", "MongoDB"
            ]
            found_tech = [tech for tech in common_tech if tech.lower() in description]
            analysis["key_technologies"] = found_tech[:10]
        
        return analysis
    
    def _add_default_fields(self, partial_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Add default values for missing fields"""
        defaults = {
            "required_skills": [],
            "preferred_skills": [],
            "experience_level": "mid",
            "min_years_experience": None,
            "max_years_experience": None,
            "education_requirements": [],
            "certifications": [],
            "responsibilities": [],
            "benefits": [],
            "salary_range": None,
            "employment_type": "full-time",
            "remote_policy": None,
            "industry": None,
            "company_size": None,
            "key_technologies": [],
            "soft_skills": []
        }
        
        for key, default_value in defaults.items():
            if key not in partial_analysis:
                partial_analysis[key] = default_value
        
        return partial_analysis
    
    def _default_response(self) -> Dict[str, Any]:
        """Default response when LLM fails completely"""
        return {
            "required_skills": [],
            "preferred_skills": [],
            "experience_level": "mid",
            "min_years_experience": None,
            "max_years_experience": None,
            "education_requirements": [],
            "certifications": [],
            "responsibilities": [],
            "benefits": [],
            "salary_range": None,
            "employment_type": "full-time",
            "remote_policy": None,
            "industry": None,
            "company_size": None,
            "key_technologies": [],
            "soft_skills": []
        }
    
    def _prepare_embedding_text(self, job_post: JobPost, analysis: Dict[str, Any]) -> str:
        """
        Prepare text for embedding generation.
        Combines title, key requirements, and responsibilities.
        """
        text_parts = [
            f"Job Title: {job_post.title}",
            f"Company: {job_post.company}",
            f"Experience Level: {analysis.get('experience_level', 'Not specified')}",
        ]
        
        # Add required skills
        required_skills = analysis.get('required_skills', [])
        if required_skills:
            text_parts.append(f"Required Skills: {', '.join(required_skills[:10])}")
        
        # Add key technologies
        key_technologies = analysis.get('key_technologies', [])
        if key_technologies:
            text_parts.append(f"Technologies: {', '.join(key_technologies[:8])}")
        
        # Add top responsibilities
        responsibilities = analysis.get('responsibilities', [])
        if responsibilities:
            top_responsibilities = ' '.join(responsibilities[:3])
            text_parts.append(f"Key Responsibilities: {top_responsibilities}")
        
        return '\n'.join(text_parts)

    def _fallback_analysis(self, job_post: JobPost) -> Dict[str, Any]:
        """Complete fallback analysis using only rule-based methods"""
        logger.warning("Using fallback analysis (LLM unavailable)")
        
        description = job_post.description.lower()
        
        # Extract basic information using regex and keywords
        analysis = self._default_response()
        
        # Try to extract years of experience
        years_match = re.search(r'(\d+)\+?\s*years?', description)
        if years_match:
            years = int(years_match.group(1))
            analysis["min_years_experience"] = years
            analysis["experience_level"] = self._detect_experience_level({"min_years_experience": years})
        
        # Extract common technologies
        common_tech = [
            "Python", "Java", "JavaScript", "TypeScript", "React", "Node.js",
            "Docker", "Kubernetes", "AWS", "Azure", "PostgreSQL", "MongoDB",
            "Git", "CI/CD", "REST", "API"
        ]
        found_tech = [tech for tech in common_tech if tech.lower() in description]
        analysis["key_technologies"] = found_tech
        analysis["required_skills"] = found_tech[:5]
        
        # Detect employment type
        if "contract" in description:
            analysis["employment_type"] = "contract"
        elif "part-time" in description or "part time" in description:
            analysis["employment_type"] = "part-time"
        elif "intern" in description:
            analysis["employment_type"] = "internship"
        
        # Detect remote policy
        if any(keyword in description for keyword in ["fully remote", "100% remote"]):
            analysis["remote_policy"] = "fully-remote"
        elif "hybrid" in description:
            analysis["remote_policy"] = "hybrid"
        elif "on-site" in description:
            analysis["remote_policy"] = "on-site"
        
        return analysis


# Singleton instance
_job_analyzer_service_instance: Optional[JobAnalyzerService] = None


def get_job_analyzer_service() -> JobAnalyzerService:
    """
    Get or create singleton Job Analyzer service instance.
    
    Returns:
        JobAnalyzerService instance
    """
    global _job_analyzer_service_instance
    if _job_analyzer_service_instance is None:
        _job_analyzer_service_instance = JobAnalyzerService()
    return _job_analyzer_service_instance
