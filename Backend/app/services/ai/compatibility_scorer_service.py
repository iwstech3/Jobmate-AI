import json
import logging
from typing import Dict, Any, List, Optional
from app.services.ai.llm_service import get_llm_service
from app.models.job_post import JobPost
from app.schemas.compatibility import (
    CompatibilityScore, SkillMatch, ExperienceMatch, EducationMatch,
    WorkExperienceRelevance, SemanticSimilarity, Recommendation
)
from app.schemas.job_analysis import JobAnalysisBase
from app.schemas.parsed_cv import ParsedCVBase

logger = logging.getLogger(__name__)

class CompatibilityScorerService:
    """
    Service for calculating detailed compatibility scores between candidates and jobs.
    Uses a mix of rule-based logic and LLM reasoning.
    """
    
    def __init__(self):
        self.llm_service = get_llm_service()
        
    def calculate_compatibility(
        self,
        parsed_cv: ParsedCVBase,
        job_analysis: JobAnalysisBase,
        job_post: JobPost,
        semantic_similarity: float
    ) -> CompatibilityScore:
        """
        Calculate comprehensive compatibility score.
        """
        # 1. Identify Critical Skills (LLM)
        critical_skills = self._identify_critical_skills(job_post.description, job_analysis.required_skills)
        
        # 2. Calculate Component Scores
        skill_match = self._calculate_skill_match(
            parsed_cv.skills, 
            job_analysis.required_skills, 
            job_analysis.preferred_skills,
            critical_skills
        )
        
        experience_match = self._calculate_experience_match(
            parsed_cv.experience_years,
            job_analysis.min_years_experience,
            job_analysis.max_years_experience
        )
        
        education_match = self._calculate_education_match(
            parsed_cv.education,
            job_analysis.education_requirements
        )
        
        work_history_relevance = self._analyze_work_experience(
            parsed_cv.work_experience,
            job_post
        )
        
        semantic_score = SemanticSimilarity(
            score=semantic_similarity,
            interpretation=self._interpret_semantic_score(semantic_similarity)
        )
        
        # 3. Calculate Weighted Overall Score
        # Weights: Skills (40%), Experience (25%), Education (15%), Work Relevance (10%), Semantic (10%)
        overall_score = (
            (skill_match.score * 100 * 0.40) +
            (experience_match.score * 100 * 0.25) +
            (education_match.score * 100 * 0.15) +
            (work_history_relevance.score * 100 * 0.10) +
            (semantic_score.score * 100 * 0.10)
        )
        overall_score = round(overall_score)
        
        # 4. Generate Recommendations & Strengths/Weaknesses
        recommendation_level = self._get_recommendation_level(overall_score)
        strengths, weaknesses = self._generate_strengths_weaknesses(
            skill_match, experience_match, education_match, work_history_relevance, semantic_score
        )
        
        # 5. Formulate Recommendations
        recommendations = self._generate_recommendations(weaknesses, skill_match.critical_missing)

        # 6. Check Interview Focus Areas
        focus_areas = self._generate_interview_focus(skill_match, experience_match, work_history_relevance)

        return CompatibilityScore(
            overall_score=overall_score,
            match_percentage=overall_score,
            recommendation=recommendation_level,
            skill_match=skill_match,
            experience_match=experience_match,
            education_match=education_match,
            work_experience_relevance=work_history_relevance,
            semantic_similarity=semantic_score,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            interview_focus_areas=focus_areas
        )

    def _identify_critical_skills(self, job_description: str, required_skills: List[str]) -> List[str]:
        """Use LLM to identify which required skills are absolutely critical."""
        if not required_skills:
            return []
            
        try:
            prompt = f"""
            Given these required skills for a job: {required_skills}
            And this job description: {job_description[:1000]}...

            Identify which of the required skills are CRITICAL (must-have) vs just important.
            Return JSON: {{"critical": ["skill1", "skill2"]}}
            """
            response = self.llm_service.generate_structured(prompt, output_format="json")
            data = json.loads(self.llm_service._clean_json(response) if hasattr(self.llm_service, '_clean_json') else response.strip('`json\n '))
            return data.get("critical", [])
        except Exception as e:
            logger.warning(f"Critical skill detection failed: {e}")
            return required_skills[:3] # Fallback: assume first 3 are critical

    def _calculate_skill_match(
        self, 
        candidate_skills: List[str], 
        required: List[str], 
        preferred: List[str],
        critical: List[str]
    ) -> SkillMatch:
        if not required:
            return SkillMatch(
                score=1.0, matched_required=[], missing_required=[], 
                matched_preferred=[], missing_preferred=[], additional_skills=[],
                match_rate=1.0, critical_missing=[]
            )

        c_skills_lower = {s.lower().strip() for s in candidate_skills}
        
        matched_req = [s for s in required if s.lower().strip() in c_skills_lower]
        missing_req = [s for s in required if s.lower().strip() not in c_skills_lower]
        matched_pref = [s for s in preferred if s.lower().strip() in c_skills_lower]
        missing_pref = [s for s in preferred if s.lower().strip() not in c_skills_lower]
        
        critical_missing = [s for s in missing_req if s in critical]
        
        # Scoring Logic
        # Start with base score based on coverage
        coverage = len(matched_req) / len(required)
        
        # Penalize for missing critical skills
        penalty = len(critical_missing) * 0.15
        
        # Bonus for preferred skills
        bonus = len(matched_pref) * 0.05
        
        score = min(1.0, max(0.0, coverage - penalty + bonus))
        
        # Identify additional skills (not in required/preferred)
        all_job_skills = set(s.lower() for s in required + preferred)
        additional = [s for s in candidate_skills if s.lower().strip() not in all_job_skills]

        return SkillMatch(
            score=round(score, 2),
            matched_required=matched_req,
            missing_required=missing_req,
            matched_preferred=matched_pref,
            missing_preferred=missing_pref,
            additional_skills=additional[:5], # Top 5 extra
            match_rate=round(coverage, 2),
            critical_missing=critical_missing
        )

    def _calculate_experience_match(
        self, 
        candidate_years: int, 
        min_years: Optional[int], 
        max_years: Optional[int]
    ) -> ExperienceMatch:
        candidate_years = candidate_years or 0
        min_years = min_years or 0
        
        gap = 0
        score = 1.0
        details = ""
        assessment = "meets_requirement"

        if candidate_years >= min_years:
            if max_years and candidate_years > max_years + 5:
                score = 0.95 # Slight Overqualification penalty?
                assessment = "exceeds"
                details = f"{candidate_years} years exceeds requirement significantly."
            else:
                score = 1.0
                assessment = "meets_requirement" if candidate_years == min_years else "exceeds"
                details = f"{candidate_years} years meets the {min_years}+ years requirement."
        else:
            gap = min_years - candidate_years
            if gap <= 1:
                score = 0.85
                assessment = "slightly_below"
                details = f"{candidate_years} years is slightly below the {min_years} years requirement."
            elif gap <= 2:
                score = 0.70
                assessment = "significantly_below"
                details = f"Missing 2 years of required experience."
            else:
                score = 0.50
                assessment = "significantly_below"
                details = f"Significant experience gap ({gap} years)."

        return ExperienceMatch(
            score=score,
            candidate_years=candidate_years,
            required_years=min_years,
            gap=gap,
            assessment=assessment,
            details=details
        )

    def _calculate_education_match(self, candidate_edu: List[Any], required_edu: List[str]) -> EducationMatch:
        # Simple string matching for now, could be enhanced with LLM
        if not required_edu:
            return EducationMatch(score=1.0, candidate_education=[], required_education=[], meets_requirement=True)

        # Flatten candidate education to strings
        c_degrees = [f"{e.degree} in {e.institution}" for e in candidate_edu] if candidate_edu else []
        
        # Check if any required keywords appear in candidate degrees
        # Very basic check
        matched = False
        for req in required_edu:
            req_lower = req.lower()
            for deg in c_degrees:
                if req_lower in deg.lower():
                    matched = True
                    break
        
        score = 1.0 if matched else 0.7 # 0.7 if no exact match but maybe educated
        if not c_degrees and required_edu:
            score = 0.4
            
        return EducationMatch(
            score=score,
            candidate_education=c_degrees,
            required_education=required_edu,
            meets_requirement=matched
        )

    def _analyze_work_experience(self, work_history: List[Any], job_post: JobPost) -> WorkExperienceRelevance:
        # Use LLM to judge relevance
        if not work_history:
            return WorkExperienceRelevance(
                score=0.5, relevant_positions=0, total_positions=0, 
                recent_experience_relevant=False, career_progression="Unclear"
            )
            
        try:
            history_summary = "\n".join([f"- {w.title} at {w.company} ({w.duration})" for w in work_history[:3]])
            prompt = f"""
            Job: {job_post.title} at {job_post.company}
            Description: {job_post.description[:300]}...
            
            Candidate History:
            {history_summary}
            
            Evaluate relevance (0-100), relevant count, recent relevant (bool), and progression (string).
            Return JSON: {{"score": 85, "relevant_count": 2, "recent_relevant": true, "progression": "Positive"}}
            """
            
            response = self.llm_service.generate_structured(prompt, output_format="json")
            # Cleaning logic if needed, usually generate_structured tries to be safe
            data = json.loads(response.strip('`json\n '))
            
            return WorkExperienceRelevance(
                score=data.get("score", 70) / 100.0,
                relevant_positions=data.get("relevant_count", 0),
                total_positions=len(work_history),
                recent_experience_relevant=data.get("recent_relevant", False),
                career_progression=data.get("progression", "Stable")
            )
        except Exception:
            # Fallback
            return WorkExperienceRelevance(
                score=0.7, relevant_positions=1, total_positions=len(work_history),
                recent_experience_relevant=True, career_progression="Standard"
            )

    def _interpret_semantic_score(self, score: float) -> str:
        if score > 0.85: return "Very strong semantic match"
        if score > 0.70: return "Strong match"
        if score > 0.50: return "Moderate match"
        return "Low semantic match"

    def _get_recommendation_level(self, score: int) -> str:
        if score >= 85: return "highly_recommended"
        if score >= 70: return "recommended"
        if score >= 55: return "potential_fit"
        return "not_recommended"

    def _generate_strengths_weaknesses(self, skill, exp, edu, work, sem) -> tuple:
        strengths = []
        weaknesses = []
        
        # Skills
        if skill.score > 0.8: strengths.append("Strong technical skill match")
        if skill.critical_missing: weaknesses.append(f"Missing critical skills: {', '.join(skill.critical_missing)}")
        
        # Experience
        if exp.assessment == "meets_requirement" or exp.assessment == "exceeds":
            strengths.append(exp.details)
        else:
            weaknesses.append(exp.details)
            
        # Education
        if edu.meets_requirement: strengths.append("Education requirements met")
        
        # Work
        if work.score > 0.8: strengths.append("Highly relevant work history")
        
        # Semantic
        if sem.score > 0.8: strengths.append("Resume content strongly aligns with job description")
        
        return strengths, weaknesses

    def _generate_recommendations(self, weaknesses: List[str], missing_skills: List[str]) -> List[Recommendation]:
        recs = []
        if missing_skills:
            recs.append(Recommendation(
                type="for_candidate", priority="high", 
                recommendation=f"Consider upskilling in: {', '.join(missing_skills[:3])}"
            ))
            recs.append(Recommendation(
                type="for_hr", priority="medium",
                recommendation=f"Probe depth of knowledge in {', '.join(missing_skills[:3])} during interview"
            ))
            
        if not recs and not weaknesses:
            recs.append(Recommendation(
                type="for_hr", priority="high", recommendation="Proceed to interview ideally."
            ))
            
        return recs

    def _generate_interview_focus(self, skill, exp, work) -> List[str]:
        areas = []
        if skill.missing_required:
            areas.append(f"Verify knowledge gaps in: {', '.join(skill.missing_required[:2])}")
        if exp.gap > 0:
            areas.append("discuss ability to ramp up given experience gap")
            
        areas.append("Career progression and recent projects")
        return areas

# Singleton
_compatibility_service_instance: Optional[CompatibilityScorerService] = None

def get_compatibility_scorer_service() -> CompatibilityScorerService:
    global _compatibility_service_instance
    if _compatibility_service_instance is None:
        _compatibility_service_instance = CompatibilityScorerService()
    return _compatibility_service_instance
