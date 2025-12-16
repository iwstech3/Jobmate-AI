import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.db import Base, get_db

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

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_analytics_flow(setup_db):
    # 1. Create a Job Post
    job_payload = {
        "title": "Test Analytics Job",
        "company": "Analytics Corp",
        "description": "Testing the analytics flow.",
        "location": "Remote",
        "job_type": "Full-time"
    }
    response = client.post("/api/v1/jobs/", json=job_payload)
    assert response.status_code == 201
    job_id = response.json()["id"]

    # 2. View the Job (Track counts)
    # View 1
    client.get(f"/api/v1/jobs/{job_id}")
    # View 2
    client.get(f"/api/v1/jobs/{job_id}", headers={"User-Agent": "TestAgent"})

    # 3. Check Stats
    response = client.get(f"/api/v1/jobs/{job_id}/stats")
    assert response.status_code == 200
    stats = response.json()
    
    assert stats["views_count"] == 2
    # applications and saves should be 0
    assert stats["applications_count"] == 0
    assert stats["saves_count"] == 0
    
    # 4. Check Analytics Overview for this job
    response = client.get(f"/api/v1/jobs/{job_id}/analytics")
    assert response.status_code == 200
    analytics = response.json()
    assert analytics["total_views"] == 2
    
    # 5. Check Trending
    response = client.get("/api/v1/jobs/trending?limit=5")
    assert response.status_code == 200
    trending = response.json()
    # Our job should be in trending as it has views
    found = any(job["id"] == job_id for job in trending)
    assert found

    # 6. Check Dashboard
    response = client.get("/api/v1/analytics/dashboard")
    assert response.status_code == 200
    dashboard = response.json()
    assert dashboard["total_views"] >= 2
    
    print("\nAnalytics integration test passed!")
