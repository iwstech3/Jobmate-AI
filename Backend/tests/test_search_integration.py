# Standalone test script to verify search features
import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import sys

# Import app components (requires DATABASE_URL set above)
try:
    from app.main import app
    from app.database.db import Base, get_db
    from app.models.job_post import JobPost
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

# Setup in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
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

def setup_data():
    Base.metadata.create_all(bind=engine)
    
    # Pre-populate data
    db = TestingSessionLocal()
    
    # Clear existing data if any (in memory valid only per run)
    
    jobs_data = [
        {
            "title": "Senior Python Developer",
            "company": "TechCorp",
            "location": "Remote",
            "job_type": "Full-time",
            "description": "Expert Python needed. Remote work available.",
            "status": "published",
            "featured": True,
            "created_at": datetime.utcnow(),
            "views_count": 100
        },
        {
            "title": "Frontend Engineer",
            "company": "StartupHub",
            "location": "Yaoundé",
            "job_type": "Contract",
            "description": "React developer needed onsite.",
            "status": "published",
            "featured": False,
            "created_at": datetime.utcnow() - timedelta(days=2),
            "views_count": 50
        },
        {
            "title": "Backend Intern",
            "company": "TechCorp",
            "location": "Douala",
            "job_type": "Internship",
            "description": "Java backend.",
            "status": "draft",
            "featured": False,
            "created_at": datetime.utcnow() - timedelta(days=5),
            "views_count": 10
        },
        {
             "title": "Remote Data Scientist",
             "company": "DataAI",
             "location": "Paris", 
             "job_type": "Full-time",
             "description": "AI and ML role. Fully remote.",
             "status": "published",
             "featured": True,
             "created_at": datetime.utcnow() - timedelta(days=1),
             "views_count": 200
        }
    ]
    
    for job in jobs_data:
        db_job = JobPost(**job)
        db.add(db_job)
    
    db.commit()
    db.close()

def run_tests():
    print("Running search integration tests...")
    
    setup_data()
    
    try:
        # 1. Search by Keyword
        response = client.get("/api/v1/jobs/search?q=Python")
        assert response.status_code == 200, f"Keyword search failed: {response.text}"
        data = response.json()
        assert data["total"] == 1, f"Expected 1 job, got {data['total']}"
        assert data["jobs"][0]["title"] == "Senior Python Developer"
        print("✓ Keyword Search Passed")

        # 2. Filter by Company
        response = client.get("/api/v1/jobs/search?company=TechCorp")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1, "Company filter failed"
        assert data["jobs"][0]["status"] == "published"
        print("✓ Company Filter Passed")
        
        # 3. Filter by Company + Status=All
        response = client.get("/api/v1/jobs/search?company=TechCorp&status=all")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        print("✓ Status Filter Passed")

        # 4. Filter by Remote
        response = client.get("/api/v1/jobs/search?is_remote=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        print("✓ Remote Filter Passed")
        
        # 5. Filter Featured
        response = client.get("/api/v1/jobs/search?is_featured=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        print("✓ Featured Filter Passed")
        
        # 6. Sorting (Views Desc)
        response = client.get("/api/v1/jobs/search?sort_by=views_count&sort_order=desc")
        data = response.json()
        assert data["jobs"][0]["views_count"] == 200
        assert data["jobs"][1]["views_count"] == 100
        print("✓ Sorting Passed")

        # 7. Shortcut: Recent
        response = client.get("/api/v1/jobs/recent")
        assert response.status_code == 200
        print("✓ Recent Jobs Endpoint Passed")
        
        # 8. Filter Options
        response = client.get("/api/v1/jobs/filters/options")
        assert response.status_code == 200
        opts = response.json()
        assert "Remote" in opts["locations"]
        assert "TechCorp" in opts["companies"]
        assert opts["counts"]["remote_count"] >= 2
        print("✓ Filter Options Endpoint Passed")
        
        print("\nALL TESTS PASSED!")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
