"""
CV Analyzer Service
Evaluates CV quality and provides improvement suggestions using Gemini LLM
"""

import json
import logging
from typing import Dict, Any, List, Optional
from app.services.ai.llm_service import get_llm_service
from app.models.parsed_cv import ParsedCV

logger = logging.getLogger(__name__)


class CVAnalyzerService:
    """
    CV Analyzer Service - evaluates CV quality and provides actionable suggestions.
    Uses both rule-based scoring and Gemini LLM for comprehensive analysis.
    """
    
    def __init__(self):
        """Initialize CV Analyzer with LLM service"""
        self.llm_service = get_llm_service()
        
    def analyze_cv(self, parsed_cv: ParsedCV) -> Dict[str, Any]:
        """
        Analyze a parsed CV and return comprehensive quality assessment.
        
        Args:
            parsed_cv: ParsedCV model instance
            
        Returns:
            Dictionary with scores, strengths, weaknesses, and suggestions
        """
        logger.info(f"Starting CV analysis for ParsedCV ID: {parsed_cv.id}")
        
        try:
            # 1. Calculate completeness score (rule-based)
            completeness_score = self._calculate_completeness_score(parsed_cv)
            logger.info(f"Completeness score: {completeness_score}")
            
            # 2. Analyze with LLM for quality, ATS, and detailed feedback
            llm_analysis = self._analyze_with_llm(parsed_cv)
            
            # 3. Analyze skills
            skill_analysis = self._analyze_skills(parsed_cv)
            
            # 4. Analyze experience
            experience_analysis = self._analyze_experience(parsed_cv)
            
            # 5. Calculate overall score
            quality_score = llm_analysis.get("quality_score", 70)
            ats_score = llm_analysis.get("ats_score", 70)
            overall_score = round((completeness_score + quality_score + ats_score) / 3)
            
            # 6. Compile complete analysis
            analysis = {
                "overall_score": overall_score,
                "completeness_score": completeness_score,
                "quality_score": quality_score,
                "ats_score": ats_score,
                "strengths": llm_analysis.get("strengths", []),
                "weaknesses": llm_analysis.get("weaknesses", []),
                "suggestions": llm_analysis.get("suggestions", []),
                "skill_analysis": skill_analysis,
                "experience_analysis": experience_analysis
            }
            
            logger.info(f"CV analysis completed. Overall score: {overall_score}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error during CV analysis: {str(e)}", exc_info=True)
            # Fallback to rule-based analysis only
            return self._fallback_analysis(parsed_cv)
    
    def _calculate_completeness_score(self, parsed_cv: ParsedCV) -> int:
        """
        Calculate completeness score based on presence of key CV sections.
        
        Args:
            parsed_cv: ParsedCV model instance
            
        Returns:
            Completeness score (0-100)
        """
        score = 0
        
        # Name (20 points)
        if parsed_cv.name and len(parsed_cv.name.strip()) > 0:
            score += 20
            
        # Email (15 points)
        if parsed_cv.email and "@" in parsed_cv.email:
            score += 15
            
        # Phone (10 points)
        if parsed_cv.phone and len(parsed_cv.phone.strip()) > 0:
            score += 10
            
        # Skills (20 points)
        if parsed_cv.skills and len(parsed_cv.skills) >= 3:
            score += 20
        elif parsed_cv.skills and len(parsed_cv.skills) > 0:
            score += 10  # Partial credit
            
        # Work experience (20 points)
        if parsed_cv.work_experience and len(parsed_cv.work_experience) > 0:
            score += 20
        elif parsed_cv.experience_years and parsed_cv.experience_years > 0:
            score += 10  # Partial credit if years mentioned
            
        # Education (10 points)
        if parsed_cv.education and len(parsed_cv.education) > 0:
            score += 10
            
        # Summary (5 points)
        if parsed_cv.summary and len(parsed_cv.summary.strip()) > 20:
            score += 5
            
        return min(score, 100)
    
    def _analyze_with_llm(self, parsed_cv: ParsedCV) -> Dict[str, Any]:
        """
        Use Gemini LLM to analyze CV quality and provide detailed feedback.
        
        Args:
            parsed_cv: ParsedCV model instance
            
        Returns:
            Dictionary with quality_score, ats_score, strengths, weaknesses, suggestions
        """
        try:
            # Prepare CV data for LLM
            work_exp_str = self._format_work_experience(parsed_cv.work_experience) if parsed_cv.work_experience else "Not provided"
            education_str = self._format_education(parsed_cv.education) if parsed_cv.education else "Not provided"
            skills_str = ", ".join(parsed_cv.skills) if parsed_cv.skills else "Not provided"
            
            system_message = "You are an expert CV/resume reviewer and career coach with 15+ years of experience in recruitment and talent acquisition."
            
            prompt = f"""Analyze this CV and provide detailed, actionable feedback. Return ONLY valid JSON with no markdown formatting.

CV Data:
Name: {parsed_cv.name or 'Not provided'}
Email: {parsed_cv.email or 'Not provided'}
Phone: {parsed_cv.phone or 'Not provided'}
Skills: {skills_str}
Experience: {parsed_cv.experience_years or 0} years
Work History:
{work_exp_str}

Education:
{education_str}

Professional Summary: {parsed_cv.summary or 'Not provided'}

Certifications: {', '.join(parsed_cv.certifications) if parsed_cv.certifications else 'None listed'}

Evaluate this CV and return JSON with:
{{
  "quality_score": <0-100 integer>,
  "ats_score": <0-100 integer>,
  "strengths": [<list of 3-5 specific strengths>],
  "weaknesses": [<list of 3-5 specific weaknesses>],
  "suggestions": [
    {{
      "category": "<skills|experience|format|content|contact_info|achievements>",
      "priority": "<high|medium|low>",
      "suggestion": "<specific actionable advice>"
    }}
  ],
  "skill_level": "<beginner|intermediate|advanced|expert>",
  "career_progression": "<positive|lateral|unclear>"
}}

Focus on:
- ATS compatibility (keywords, formatting, structure)
- Professional presentation and clarity
- Quantifiable achievements and impact
- Completeness of information
- Industry best practices"""

            response = self.llm_service.generate_structured(prompt, system_message=system_message, output_format="json")
            
            # Clean and parse JSON
            cleaned_response = self._clean_json_response(response)
            parsed_response = json.loads(cleaned_response)
            
            logger.info("LLM analysis successful")
            return parsed_response
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}. Response: {response[:200]}")
            # Retry once with simpler prompt
            return self._simple_llm_analysis(parsed_cv)
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}", exc_info=True)
            return self._default_llm_response()
    
    def _simple_llm_analysis(self, parsed_cv: ParsedCV) -> Dict[str, Any]:
        """Simplified LLM analysis as fallback"""
        try:
            prompt = f"""Rate this CV on a scale of 0-100 for quality and ATS-friendliness. List 3 strengths and 3 weaknesses.

Name: {parsed_cv.name}
Skills: {len(parsed_cv.skills) if parsed_cv.skills else 0} skills listed
Experience: {parsed_cv.experience_years or 0} years

Return JSON only:
{{
  "quality_score": 75,
  "ats_score": 70,
  "strengths": ["strength1", "strength2", "strength3"],
  "weaknesses": ["weakness1", "weakness2", "weakness3"]
}}"""
            
            response = self.llm_service.generate_structured(prompt, output_format="json")
            cleaned = self._clean_json_response(response)
            result = json.loads(cleaned)
            
            # Add default suggestions
            result["suggestions"] = self._generate_default_suggestions(parsed_cv)
            result["skill_level"] = "intermediate"
            result["career_progression"] = "unclear"
            
            return result
        except:
            return self._default_llm_response()
    
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
    
    def _default_llm_response(self) -> Dict[str, Any]:
        """Default response when LLM fails"""
        return {
            "quality_score": 70,
            "ats_score": 70,
            "strengths": ["CV structure is present", "Contact information provided"],
            "weaknesses": ["Could benefit from more detailed analysis", "Consider adding more quantifiable achievements"],
            "suggestions": [
                {"category": "content", "priority": "medium", "suggestion": "Add more specific achievements with metrics"},
                {"category": "skills", "priority": "medium", "suggestion": "Expand skills section with relevant technologies"}
            ],
            "skill_level": "intermediate",
            "career_progression": "unclear"
        }
    
    def _analyze_skills(self, parsed_cv: ParsedCV) -> Dict[str, Any]:
        """
        Analyze and categorize skills.
        
        Args:
            parsed_cv: ParsedCV model instance
            
        Returns:
            Skill analysis dictionary
        """
        skills = parsed_cv.skills or []
        
        # Common technical keywords
        technical_keywords = {
            "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go", "rust",
            "react", "angular", "vue", "node", "django", "flask", "fastapi", "spring",
            "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
            "docker", "kubernetes", "aws", "azure", "gcp", "terraform",
            "git", "ci/cd", "jenkins", "github", "gitlab",
            "machine learning", "ai", "data science", "tensorflow", "pytorch"
        }
        
        # Common soft skills keywords
        soft_keywords = {
            "leadership", "communication", "teamwork", "problem solving", "analytical",
            "project management", "agile", "scrum", "collaboration", "mentoring"
        }
        
        technical_skills = []
        soft_skills = []
        
        for skill in skills:
            skill_lower = skill.lower()
            if any(tech in skill_lower for tech in technical_keywords):
                technical_skills.append(skill)
            elif any(soft in skill_lower for soft in soft_keywords):
                soft_skills.append(skill)
            else:
                # Default to technical if unclear
                technical_skills.append(skill)
        
        # Determine skill level
        skill_count = len(skills)
        years = parsed_cv.experience_years or 0
        
        if years >= 8 and skill_count >= 15:
            skill_level = "expert"
        elif years >= 5 and skill_count >= 10:
            skill_level = "advanced"
        elif years >= 2 and skill_count >= 5:
            skill_level = "intermediate"
        else:
            skill_level = "beginner"
        
        # Suggest missing common skills (simplified)
        all_skills_lower = [s.lower() for s in skills]
        missing_skills = []
        
        common_must_haves = ["git", "docker", "sql", "rest api", "testing"]
        for skill in common_must_haves:
            if not any(skill in s for s in all_skills_lower):
                missing_skills.append(skill.title())
        
        return {
            "technical_skills": technical_skills,
            "soft_skills": soft_skills,
            "skill_level": skill_level,
            "missing_common_skills": missing_skills[:5]  # Top 5
        }
    
    def _analyze_experience(self, parsed_cv: ParsedCV) -> Dict[str, Any]:
        """
        Analyze career progression and experience quality.
        
        Args:
            parsed_cv: ParsedCV model instance
            
        Returns:
            Experience analysis dictionary
        """
        years = parsed_cv.experience_years or 0
        work_exp = parsed_cv.work_experience or []
        
        # Determine career progression
        if len(work_exp) >= 2:
            # Check if titles show progression (simplified heuristic)
            titles = [exp.get("title", "").lower() for exp in work_exp]
            senior_keywords = ["senior", "lead", "principal", "architect", "manager", "director"]
            
            has_senior_role = any(any(kw in title for kw in senior_keywords) for title in titles)
            career_progression = "positive" if has_senior_role else "lateral"
        else:
            career_progression = "unclear"
        
        # Assess recent experience relevance (simplified)
        recent_experience = "relevant" if len(work_exp) > 0 else "not_relevant"
        
        # Job stability
        if len(work_exp) == 0:
            job_stability = "unclear"
        elif years > 0 and len(work_exp) > 0:
            avg_tenure = years / len(work_exp)
            if avg_tenure >= 3:
                job_stability = "excellent"
            elif avg_tenure >= 1.5:
                job_stability = "good"
            else:
                job_stability = "concerning"
        else:
            job_stability = "good"
        
        return {
            "total_years": years,
            "career_progression": career_progression,
            "recent_experience": recent_experience,
            "job_stability": job_stability
        }
    
    def _generate_default_suggestions(self, parsed_cv: ParsedCV) -> List[Dict[str, str]]:
        """Generate basic suggestions based on missing fields"""
        suggestions = []
        
        if not parsed_cv.phone:
            suggestions.append({
                "category": "contact_info",
                "priority": "high",
                "suggestion": "Add phone number for better reachability"
            })
        
        if not parsed_cv.skills or len(parsed_cv.skills) < 5:
            suggestions.append({
                "category": "skills",
                "priority": "high",
                "suggestion": "Add more relevant skills to improve ATS matching"
            })
        
        if not parsed_cv.summary or len(parsed_cv.summary) < 50:
            suggestions.append({
                "category": "content",
                "priority": "medium",
                "suggestion": "Add a compelling professional summary (2-3 sentences)"
            })
        
        if not parsed_cv.certifications or len(parsed_cv.certifications) == 0:
            suggestions.append({
                "category": "achievements",
                "priority": "low",
                "suggestion": "Consider adding relevant certifications to stand out"
            })
        
        return suggestions
    
    def _fallback_analysis(self, parsed_cv: ParsedCV) -> Dict[str, Any]:
        """Complete fallback analysis using only rule-based methods"""
        logger.warning("Using fallback analysis (LLM unavailable)")
        
        completeness_score = self._calculate_completeness_score(parsed_cv)
        skill_analysis = self._analyze_skills(parsed_cv)
        experience_analysis = self._analyze_experience(parsed_cv)
        
        # Simple quality estimation
        quality_score = completeness_score
        ats_score = min(completeness_score + 10, 100)
        overall_score = round((completeness_score + quality_score + ats_score) / 3)
        
        return {
            "overall_score": overall_score,
            "completeness_score": completeness_score,
            "quality_score": quality_score,
            "ats_score": ats_score,
            "strengths": ["CV structure is present", "Basic information provided"],
            "weaknesses": ["Detailed analysis unavailable", "Consider manual review"],
            "suggestions": self._generate_default_suggestions(parsed_cv),
            "skill_analysis": skill_analysis,
            "experience_analysis": experience_analysis
        }
    
    def _format_work_experience(self, work_exp: List[Dict]) -> str:
        """Format work experience for LLM prompt"""
        if not work_exp:
            return "No work experience provided"
        
        formatted = []
        for exp in work_exp[:5]:  # Limit to 5 most recent
            title = exp.get("title", "Unknown")
            company = exp.get("company", "Unknown")
            duration = exp.get("duration", "Unknown")
            description = exp.get("description", "")
            formatted.append(f"- {title} at {company} ({duration})\n  {description[:200]}")
        
        return "\n".join(formatted)
    
    def _format_education(self, education: List[Dict]) -> str:
        """Format education for LLM prompt"""
        if not education:
            return "No education provided"
        
        formatted = []
        for edu in education:
            degree = edu.get("degree", "Unknown")
            institution = edu.get("institution", "Unknown")
            year = edu.get("year", "Unknown")
            formatted.append(f"- {degree}, {institution} ({year})")
        
        return "\n".join(formatted)


# Singleton instance
_cv_analyzer_service_instance: Optional[CVAnalyzerService] = None


def get_cv_analyzer_service() -> CVAnalyzerService:
    """
    Get or create singleton CV Analyzer service instance.
    
    Returns:
        CVAnalyzerService instance
    """
    global _cv_analyzer_service_instance
    if _cv_analyzer_service_instance is None:
        _cv_analyzer_service_instance = CVAnalyzerService()
    return _cv_analyzer_service_instance
