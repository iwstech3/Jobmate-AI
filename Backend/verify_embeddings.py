import sys
import json
import urllib.request
import urllib.error
import time

BASE_URL = "http://localhost:8001/api/v1"

def create_job():
    url = f"{BASE_URL}/jobs/"
    data = {
        "title": "AI Engineer Test",
        "company": "Tech Corp",
        "description": "We need an AI engineer with Python, PyTorch, and NLP skills. Experience with LLMs is a plus.",
        "location": "Remote",
        "job_type": "Full-time"
    }
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError as e:
        print(f"Error creating job: {e}")
        return None

def analyze_job(job_id):
    url = f"{BASE_URL}/jobs/{job_id}/analyze"
    req = urllib.request.Request(
        url,
        data=b"", # Empty body for POST
        headers={'Content-Type': 'application/json'},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Error analyzing job: {e.code}")
        try:
            print(e.read().decode())
        except:
            pass
        return None
    except urllib.error.URLError as e:
        print(f"Connection error: {e}")
        return None

def main():
    print("Checking if server is up...")
    try:
        urllib.request.urlopen(f"{BASE_URL}/jobs/filters/options", timeout=2)
    except:
        print("Server not accessible at http://localhost:8001. Please start it first.")
        return

    print("1. Creating test job...")
    job = create_job()
    if not job:
        print("Failed to create job.")
        return

    job_id = job['id']
    print(f"Job created with ID: {job_id}")

    print(f"2. Analyzing job {job_id}...")
    result = analyze_job(job_id)
    
    if result:
        print("\nAnalysis Result:")
        print(f"Embedding Created: {result.get('embedding_created')}")
        print(f"Dimensions: {result.get('embedding_dimensions')}")
        
        if result.get('embedding_created'):
            print("\nSUCCESS: Embedding was successfully created!")
        else:
            print("\nFAILURE: Embedding flag not true. Check logs.")
    else:
        print("\nFAILURE: Analysis request failed.")

if __name__ == "__main__":
    main()
