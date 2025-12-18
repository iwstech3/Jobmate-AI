from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, select
import logging
import json

from app.models.parsed_cv import ParsedCV
from app.models.document_embedding import DocumentEmbedding
from app.models.job_post import JobPost
from app.models.job_analysis import JobAnalysis
from app.models.job_embedding import JobEmbedding
from app.models.document import Document

from app.services.ai.compatibility_scorer_service import get_compatibility_scorer_service
from app.schemas.job_match import JobMatchList

logger = logging.getLogger(__name__)

class JobMatcherService:
    """
    Service for semantic matching of candidates to jobs and vice versa.
    Uses vector similarity (via pgvector) and detailed compatibility scoring.
    """
    
    def __init__(self):
        self.scorer = get_compatibility_scorer_service()

    def find_matching_jobs(self, db: Session, parsed_cv_id: int, limit: int = 10, min_score: float = 0.0) -> List[Dict[str, Any]]:
        """
        Finds the best matching jobs for a specific candidate (ParsedCV).
        
        Args:
            db: Database session
            parsed_cv_id: ID of the ParsedCV to match
            limit: Maximum number of results to return
            min_score: Minimum overall match score to include
            
        Returns:
            List of match dictionaries
        """
        # 1. Get Candidate Data
        candidate_data = self._get_candidate_data(db, parsed_cv_id)
        if not candidate_data:
            logger.warning(f"ParsedCV with id {parsed_cv_id} not found or missing embedding.")
            return []
            
        candidate_embedding = candidate_data['embedding']
        candidate_skills = candidate_data['skills']
        candidate_experience = candidate_data.get('experience_years', 0) or 0
        
        # 2. Vector Search for Similar Jobs
        # Using raw SQL for efficient pgvector query with joins
        # Note: Using <=> operator for cosine distance. 1 - distance = similarity.
        query = text("""
            SELECT 
                jp.id, jp.title, jp.company, jp.location,
                je.embedding <=> :candidate_embedding as distance,
                ja.required_skills, ja.preferred_skills, 
                ja.min_years_experience, ja.max_years_experience, 
                ja.experience_level
            FROM job_posts jp
            JOIN job_embeddings je ON jp.id = je.job_post_id
            LEFT JOIN job_analyses ja ON jp.id = ja.job_post_id
            ORDER BY distance ASC
            LIMIT :limit
        """)
        
        # We fetch more than the limit initially to allow for re-ranking based on full score
        # But for now, we'll trust the semantic search to bring good candidates into the top set,
        # then refine the scoring. To be safe, we could query limit * 2.
        search_limit = limit * 2 
        
        results = db.execute(
            query, 
            {"candidate_embedding": str(candidate_embedding), "limit": search_limit}
        ).fetchall()
        
        matches = []
        
        for row in results:
            # Extract data
            job_id = row.id
            similarity_score = 1 - row.distance
            
            # Skip if vector similarity is too low? (Optional, maybe let overall score decide)
            
            # 3. Calculate Detailed Compatibility
            # Construct ephemeral objects if needed or fetch full models
            # Here we have partial data in row, but scorer wants schemas/models.
            # Best to load full objects for the top candidates after vector filter.
            
            # For efficiency in this loop, let's just fetch the JobPost and Analysis objects fully for the shortlist
            job_post = db.query(JobPost).filter(JobPost.id == job_id).first()
            job_analysis = db.query(JobAnalysis).filter(JobAnalysis.job_post_id == job_id).first()
            
            if not job_analysis:
                 # Skip or use basic scoring if analysis missing
                 continue
                 
            # Convert row data to ParsedCV schema-like object for scorer
            # (In reality, we should pass the full parsed_cv object fetched earlier)
            candidate_obj = candidate_data['obj'] # We need to store this in step 1
            
            compatibility = self.scorer.calculate_compatibility(
                parsed_cv=candidate_obj,
                job_analysis=job_analysis,
                job_post=job_post,
                semantic_similarity=similarity_score
            )
            
            if compatibility.overall_score < min_score * 100:
                continue
            
            matches.append({
                "job_id": job_id,
                "job_title": row.title,
                "company": row.company,
                "location": row.location,
                "similarity_score": round(similarity_score, 2),
                "compatibility": compatibility.dict(), # Embed full report
                # Keep legacy fields for backward compat if needed, or remove
                "overall_match_score": compatibility.overall_score,
                "match_percentage": compatibility.match_percentage,
            })
            
        # Sort by overall score descending
        matches.sort(key=lambda x: x['overall_match_score'], reverse=True)
        
        return matches[:limit]

    def find_matching_candidates(self, db: Session, job_id: int, limit: int = 10, min_score: float = 0.0) -> List[Dict[str, Any]]:
        """
        Finds the best matching candidates for a specific job.
        
        Args:
            db: Database session
            job_id: ID of the JobPost to match
            limit: Maximum number of results
            min_score: Minimum overall match score
            
        Returns:
            List of match dictionaries
        """
        # 1. Get Job Data
        job_data = self._get_job_data(db, job_id)
        if not job_data:
            logger.warning(f"JobPost with id {job_id} not found or missing embedding.")
            return []

        job_embedding = job_data['embedding']
        required_skills = job_data['required_skills']
        min_years = job_data.get('min_years_experience')
        max_years = job_data.get('max_years_experience')

        # 2. Vector Search for Similar Candidates
        query = text("""
            SELECT 
                d.id as document_id, 
                pcv.id as parsed_cv_id, pcv.name, pcv.skills, pcv.experience_years,
                de.embedding <=> :job_embedding as distance
            FROM documents d
            JOIN document_embeddings de ON d.id = de.document_id
            JOIN parsed_cvs pcv ON d.id = pcv.document_id
            ORDER BY distance ASC
            LIMIT :limit
        """)
        
        search_limit = limit * 2
        
        results = db.execute(
            query,
            {"job_embedding": str(job_embedding), "limit": search_limit}
        ).fetchall()
        
        matches = []
        
        for row in results:
            similarity_score = 1 - row.distance
            
            candidate_skills = row.skills if row.skills else []
            candidate_experience = row.experience_years if row.experience_years is not None else 0
            
            # 3. Calculate Scores
            skill_score_data = self._calculate_skill_match(candidate_skills, required_skills)
            exp_score = self._calculate_experience_match(candidate_experience, min_years, max_years)
            
            # 4. Overall Score
            overall_score = (
                similarity_score * 0.4 +
                skill_score_data['score'] * 0.4 +
                exp_score * 0.2
            )
            
            if overall_score < min_score:
                continue

            match_details = self._generate_match_details(
                overall_score, skill_score_data, exp_score, candidate_experience, min_years
            )
            
            matches.append({
                "candidate_id": row.parsed_cv_id,
                "document_id": row.document_id,
                "name": row.name or "Unknown Candidate",
                "similarity_score": round(similarity_score, 2),
                "skill_match_score": round(skill_score_data['score'], 2),
                "experience_match_score": round(exp_score, 2),
                "overall_match_score": round(overall_score, 2),
                "match_percentage": int(overall_score * 100),
                "matched_skills": skill_score_data['matched'],
                "missing_skills": skill_score_data['missing'],
                "match_explanation": match_details['explanation'],
                "recommendation": match_details['recommendation']
            })
            
        matches.sort(key=lambda x: x['overall_match_score'], reverse=True)
        return matches[:limit]


    def _get_candidate_data(self, db: Session, parsed_cv_id: int) -> Optional[Dict[str, Any]]:
        """Helper to fetch candidate data and embedding."""
        result = db.execute(
            select(ParsedCV, DocumentEmbedding.embedding)
            .join(DocumentEmbedding, ParsedCV.document_id == DocumentEmbedding.document_id)
            .where(ParsedCV.id == parsed_cv_id)
        ).first()
        
        if not result:
            return None
            
        parsed_cv, embedding = result
        return {
            "obj": parsed_cv, # Return full object
            "embedding": embedding,
            "skills": parsed_cv.skills or [],
            "experience_years": parsed_cv.experience_years
        }

    def _get_job_data(self, db: Session, job_id: int) -> Optional[Dict[str, Any]]:
        """Helper to fetch job data and embedding."""
        # Join JobPost, JobEmbedding, and JobAnalysis (optional)
        result = db.execute(
            select(JobPost, JobEmbedding.embedding, JobAnalysis)
            .join(JobEmbedding, JobPost.id == JobEmbedding.job_post_id)
            .outerjoin(JobAnalysis, JobPost.id == JobAnalysis.job_post_id)
            .where(JobPost.id == job_id)
        ).first()

        if not result:
            return None
        
        job_post, embedding, analysis = result
        
        required_skills = []
        min_years = None
        max_years = None
        
        if analysis:
            required_skills = analysis.required_skills or []
            min_years = analysis.min_years_experience
            max_years = analysis.max_years_experience
            
        return {
            "embedding": embedding,
            "required_skills": required_skills,
            "min_years_experience": min_years,
            "max_years_experience": max_years
        }

    def _calculate_skill_match(self, candidate_skills: List[str], required_skills: List[str]) -> Dict[str, Any]:
        """Calculates skill overlap score."""
        if not required_skills:
            return {"score": 1.0, "matched": [], "missing": []} # If no skills required, perfect match on that front? Or neutral?
            # If no skills are strictly required, maybe we imply 0 score, or ignore it?
            # Reverting to 0.5 or 0 might be safer, but 1.0 implies "no blockers". 
            # Let's say if no requirements, skills match is neutral/good.
            
        # Normalize
        c_skills_lower = {s.strip().lower() for s in candidate_skills}
        r_skills_lower = {s.strip().lower() for s in required_skills}
        
        matched = []
        missing = []
        
        for r_skill in required_skills:
            if r_skill.strip().lower() in c_skills_lower:
                matched.append(r_skill)
            else:
                missing.append(r_skill)
                
        # Simple Jaccard or overlap ratio? Requirement says: matched_count / total_required
        score = len(matched) / len(required_skills) if required_skills else 0.0
        
        return {
            "score": score,
            "matched": matched,
            "missing": missing
        }

    def _calculate_experience_match(self, candidate_years: int, min_years: Optional[int], max_years: Optional[int]) -> float:
        """Calculates experience match score."""
        candidate_years = candidate_years or 0
        
        if min_years is None:
            return 0.8  # Neutral/Good if not specified
            
        # If max_years is None, treat it as open-ended
        
        if candidate_years < min_years:
            # Under-qualified
            gap = min_years - candidate_years
            # Penalty: 0.2 per year missing
            return max(0.0, 1.0 - (gap * 0.2))
            
        elif max_years and candidate_years > max_years:
            # Over-qualified
            return 0.9
        else:
            # In range (or above min if no max)
            return 1.0

    def _generate_match_details(self, overall_score: float, skill_data: Dict, exp_score: float, candidate_exp: int, min_exp: Optional[int]) -> Dict[str, str]:
        """Generates recommendation and explanation string."""
        
        # Recommendation
        if overall_score >= 0.80:
            recommendation = "highly_recommended"
        elif overall_score >= 0.65:
            recommendation = "recommended"
        elif overall_score >= 0.50:
            recommendation = "potential_fit"
        else:
            recommendation = "not_recommended"
            
        # Explanation
        parts = []
        
        # Skills part
        matched_count = len(skill_data['matched'])
        total_req = matched_count + len(skill_data['missing'])
        if total_req > 0:
            parts.append(f"{matched_count}/{total_req} skills matched.")
        else:
            parts.append("No specific skills required.")
            
        # Experience part
        if exp_score >= 0.9:
            parts.append(f"Experience ({candidate_exp}y) fits well.")
        elif min_exp and candidate_exp < min_exp:
            parts.append(f"Below exp req ({min_exp}y+).")
            
        explanation = " ".join(parts)
        
        return {
            "recommendation": recommendation,
            "explanation": explanation
        }
