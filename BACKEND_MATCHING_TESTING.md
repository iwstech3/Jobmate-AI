# Semantic Job Matching - Testing Guide

This guide explains how to test the new Semantic Job Matching Agent.

## Prerequisites

Ensure you have:
1. Running PostgreSQL with `pgvector` extension (and Docker container running).
2. `GEMINI_API_KEY` set in your `.env` file.
3. At least one parsed CV and one analyzed Job Post in the database.

## 1. Automated Testing Script

We have provided a script to quickly verify the matching logic using existing data in your database.

Run the following command:

```bash
python scripts/test_job_matching.py
```

This script will:
- Connect to your database.
- Find a candidate with embeddings (ParsedCV).
- Find a job with embeddings (JobPost).
- Run matching in both directions (Job -> Candidate, Candidate -> Job).
- Print the top matches with scores and explanations.

## 2. API Testing (via Swagger UI)

1. Start the backend server:
   ```bash
   uvicorn app.main:app --reload
   ```
2. Open Swagger UI: http://localhost:8000/docs

### Test Finding Jobs for a Candidate

1. Locate `GET /api/v1/documents/{document_id}/matching-jobs`.
2. Enter a valid `document_id` of a parsed CV.
3. Execute.
4. Verify the response contains a list of jobs with `match_percentage`, `similarity_score`, and `recommendation`.

### Test Finding Candidates for a Job

1. Locate `GET /api/v1/jobs/{job_id}/matching-candidates`.
2. Enter a valid `job_id` of an analyzed Job Post.
3. Execute.
4. Verify the response contains a list of candidates.

## 3. Sample SQL Queries

You can also inspect the embeddings and basic similarity directly in SQL.

**Check Job Embeddings:**
```sql
SELECT job_post_id, substring(embedded_text for 50) as text_preview, created_at 
FROM job_embeddings 
LIMIT 5;
```

**Find Similar Jobs manually (SQL):**
```sql
-- Replace [VECTOR] with a real vector array from a document_embedding
SELECT jp.title, (1 - (je.embedding <=> '[VECTOR]')) as similarity
FROM job_posts jp
JOIN job_embeddings je ON jp.id = je.job_post_id
ORDER BY similarity DESC
LIMIT 5;
```

## Troubleshooting

- **No matches found?**
  - Ensure you have run `/analyze` on your Job Posts (creates `job_embeddings`).
  - Ensure you have run `/parse` and `/analyze` (or just text extraction?) on CVs. Note: Embeddings for CVs are created during parsing/upload? 
  - *Correction*: Embeddings for CVs are usually created during parsing or upload. Check `DocumentEmbedding` table.

- **pgvector error?**
  - Ensure the extension is enabled: `CREATE EXTENSION IF NOT EXISTS vector;`
  - Ensure your Docker container has the pgvector image.
