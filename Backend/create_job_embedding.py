"""Create embedding for existing job"""
import sys
sys.path.insert(0, '.')

from app.database.db import SessionLocal
from app.models.job_post import JobPost
from app.models.job_embedding import JobEmbedding
from app.models.job_analysis import JobAnalysis
from app.services.ai.embeddings_service import get_embeddings_service

db = SessionLocal()
embeddings = get_embeddings_service()

try:
    # Get job and its analysis
    job_id = 1  # Change this to your job ID
    job = db.query(JobPost).filter(JobPost.id == job_id).first()
    analysis = db.query(JobAnalysis).filter(JobAnalysis.job_post_id == job_id).first()
    
    if not job:
        print(f"❌ Job {job_id} not found")
        sys.exit(1)
    
    print(f"✅ Job found: {job.title}")
    
    # Build embedding text
    if analysis:
        embedding_text = f"{job.title}\n"
        embedding_text += f"Required skills: {', '.join(analysis.required_skills)}\n"
        embedding_text += f"Key technologies: {', '.join(analysis.key_technologies[:5])}\n"
        embedding_text += f"Experience level: {analysis.experience_level}"
        print(f"✅ Using analysis data")
    else:
        # Fallback to description
        embedding_text = f"{job.title}\n{job.description}"
        print(f"⚠️  No analysis found, using description")
    
    print(f"\n📝 Embedding text preview:")
    print(embedding_text[:200] + "...")
    
    # Generate embedding
    print(f"\n🔄 Generating embedding...")
    embedding_vector = embeddings.embed_document(embedding_text)
    print(f"✅ Embedding generated ({len(embedding_vector)} dimensions)")
    
    # Check if embedding already exists
    existing = db.query(JobEmbedding).filter(JobEmbedding.job_post_id == job_id).first()
    
    if existing:
        print(f"⚠️  Embedding already exists, updating...")
        existing.embedding = embedding_vector
        existing.embedded_text = embedding_text
    else:
        print(f"✅ Creating new embedding...")
        job_embedding = JobEmbedding(
            job_post_id=job_id,
            embedding=embedding_vector,
            embedded_text=embedding_text
        )
        db.add(job_embedding)
    
    db.commit()
    print(f"\n🎉 Job embedding created/updated successfully!")
    
    # Verify
    check = db.query(JobEmbedding).filter(JobEmbedding.job_post_id == job_id).first()
    print(f"✅ Verified: Embedding exists in database (ID: {check.id})")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()