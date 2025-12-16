# Standalone test script for Job Status Workflow
import os
import sys
# Force SQLite for testing
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

try:
    from app.main import app
    from app.database.db import Base, get_db
    from app.models.job_post import JobPost
    from app.models.job_status_history import JobStatusHistory
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

# Setup in-memory DB
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def setup_db():
    Base.metadata.create_all(bind=engine)

def cleanup_db():
    Base.metadata.drop_all(bind=engine)

def run_tests():
    print("Running Job Status Workflow Tests...")
    setup_db()
    
    try:
        # 1. Create a Draft Job
        print("\n[Test] Create Draft Job")
        payload = {
            "title": "Draft Engineer",
            "company": "Test Co",
            "description": "Just a draft description for testing.",
            "status": "draft"
        }
        res = client.post("/api/v1/jobs/", json=payload)
        assert res.status_code in [200, 201], f"Create failed: {res.text}"
        job_id = res.json()["id"]
        assert res.json()["status"] == "draft"
        print("✓ Created job as draft")
        
        # 2. Verify Draft visibility
        # Should appear in /drafts
        res = client.get("/api/v1/jobs/drafts")
        assert res.status_code == 200
        assert res.json()["total"] == 1
        print("✓ Visible in drafts endpoint")
        
        # Should NOT appear in /search (public)
        res = client.get("/api/v1/jobs/search?q=Draft")
        # Note: if search defaults to published only, total should be 0
        data = res.json()
        assert data["total"] == 0
        print("✓ Hidden from public search")
        
        # 3. Publish the Job
        print("\n[Test] Publish Job")
        res = client.post(f"/api/v1/jobs/{job_id}/publish")
        assert res.status_code == 200
        assert res.json()["status"] == "published"
        print("✓ Job published")
        
        # Verify history
        res = client.get(f"/api/v1/jobs/{job_id}/status-history")
        history = res.json()
        assert len(history) == 1
        assert history[0]["old_status"] == "draft"
        assert history[0]["new_status"] == "published"
        print("✓ History recorded")
        
        # 4. Close the Job (Success)
        print("\n[Test] Close Job")
        res = client.post(f"/api/v1/jobs/{job_id}/close?reason=Filled")
        assert res.status_code == 200
        assert res.json()["status"] == "closed"
        print("✓ Job closed")
        
        # 5. Invalid Transition (Closed -> Draft)
        print("\n[Test] Invalid Transition")
        res = client.put(f"/api/v1/jobs/{job_id}/status", json={"status": "draft"})
        assert res.status_code == 400
        print("✓ Prevented invalid transition (Closed -> Draft)")
        
        # 6. Reopen Job
        print("\n[Test] Reopen Job")
        res = client.post(f"/api/v1/jobs/{job_id}/reopen")
        assert res.status_code == 200
        assert res.json()["status"] == "published"
        print("✓ Job reopened")

        print("\nALL STATUS TESTS PASSED!")

    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
    finally:
        cleanup_db()

if __name__ == "__main__":
    run_tests()
