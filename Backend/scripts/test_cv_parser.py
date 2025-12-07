import requests
import json
import os

# Configuration
API_URL = "http://127.0.0.1:8002/api/v1"
TEST_FILE_PATH = "scripts/test_cv.txt"

def create_dummy_cv():
    content = """
    John Doe
    john.doe@example.com
    +1-555-0100
    
    Professional Summary
    Experienced software engineer with 5 years of experience in Python and cloud technologies.
    
    Skills
    Python, FastAPI, AWS, Docker, PostgreSQL
    
    Experience
    Senior Developer at Tech Corp (2020-Present)
    - Built scalable microservices using FastAPI.
    
    Junior Developer at StartUp Inc (2018-2020)
    - Maintained legacy Django applications.
    
    Education
    BS Computer Science, University of Technology (2018)
    
    Certifications
    AWS Certified Solutions Architect
    """
    with open(TEST_FILE_PATH, "w") as f:
        f.write(content)
    print(f"[OK] Created dummy CV at {TEST_FILE_PATH}")

def test_cv_parser():
    print("Starting CV Parser Verification...")
    
    # 1. Upload Document
    print("\n1. Uploading Document...")
    with open(TEST_FILE_PATH, "rb") as f:
        files = {"file": (os.path.basename(TEST_FILE_PATH), f, "text/plain")}
        response = requests.post(f"{API_URL}/documents/upload", files=files, params={"document_type": "cv"})
    
    if response.status_code != 201:
        print(f"[FAIL] Upload failed: {response.text}")
        return
    
    doc_data = response.json()
    document_id = doc_data["document"]["id"]
    print(f"[OK] Document uploaded with ID: {document_id}")
    
    # 2. Parse Document
    print(f"\n2. Parsing Document ID {document_id}...")
    response = requests.post(f"{API_URL}/documents/{document_id}/parse")
    
    if response.status_code != 200:
        print(f"[FAIL] Parsing failed: {response.text}")
        return
        
    parsed_data = response.json()
    print(f"[OK] Parsing successful!")
    
    # 3. Verify Data
    print("\n3. Verifying Parsed Data...")
    print(json.dumps(parsed_data, indent=2))
    
    assert parsed_data["name"] is not None, "Name should be extracted"
    assert parsed_data["email"] == "john.doe@example.com", "Email mismatch"
    assert "Python" in parsed_data["skills"], "Skills missing Python"
    
    print("\n[SUCCESS] CV Parser Service verified successfully!")

if __name__ == "__main__":
    create_dummy_cv()
    try:
        test_cv_parser()
    except Exception as e:
        print(f"\n[FAIL] Test failed with exception: {e}")
    finally:
        # Cleanup
        if os.path.exists(TEST_FILE_PATH):
            os.remove(TEST_FILE_PATH)
