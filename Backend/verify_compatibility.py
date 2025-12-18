import sys
import json
import urllib.request
import urllib.error
import time

BASE_URL = "http://localhost:8001/api/v1"

def print_section(title):
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")

def make_request(url, method="GET", data=None):
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8') if data else None,
            headers={'Content-Type': 'application/json'},
            method=method
        )
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Request Error ({url}): {e.code} - {e.reason}")
        try:
            print(e.read().decode())
        except:
            pass
        return None
    except urllib.error.URLError as e:
        print(f"Connection Error ({url}): {e.reason}")
        return None

def main():
    print_section("Compatibility Scoring Verification")
    
    # Check server
    try:
        urllib.request.urlopen(f"{BASE_URL}/jobs/filters/options", timeout=2)
    except:
        print("Server not running at http://localhost:8001. Please start it.")
        return

    # 1. Use existing Job and CV (assuming previous tests left some data)
    # Ideally find valid IDs first
    print("Finding valid CV and Job...")
    
    jobs = make_request(f"{BASE_URL}/jobs/?limit=5")
    if not jobs or not jobs['items']:
        print("No jobs found. Please create a job first.")
        return
    
    job_id = jobs['items'][0]['id']
    print(f"Using Job ID: {job_id} ({jobs['items'][0]['title']})")
    
    # Find a document/CV
    # Since we don't have a direct list documents endpoint readily available without auth maybe?
    # Let's try matching-candidates for the job to find a candidate ID
    candidates = make_request(f"{BASE_URL}/jobs/{job_id}/matching-candidates")
    
    parsed_cv_id = None
    document_id = None
    
    if candidates:
        candidate = candidates[0]
        parsed_cv_id = candidate.get('candidate_id')
        document_id = candidate.get('document_id')
        print(f"Found Candidate: CV ID {parsed_cv_id} (Doc ID {document_id})")
    else:
        print("No candidates found for this job. Verification limited.")
        # Try to find specific document 1
        doc = make_request(f"{BASE_URL}/documents/1/matching-jobs")
        if doc: 
            document_id = 1
            # We don't know the parsed_cv_id easily without an endpoint, but for documents/1/matching-jobs we just need doc id
            print("Using Document ID 1 for reverse check.")
        else:
            print("Could not find any candidates/documents.")
            return

    # 2. Test Enhanced Matching Endpoint
    if document_id:
        print_section("Testing Enhanced Matching Endpoint")
        print(f"GET /documents/{document_id}/matching-jobs")
        matches = make_request(f"{BASE_URL}/documents/{document_id}/matching-jobs?limit=3")
        
        if matches and matches.get('matches'):
            first_match = matches['matches'][0]
            print(f"Top Match: {first_match['job_title']}")
            print(f"Overall Score: {first_match['overall_match_score']}")
            
            if 'compatibility' in first_match and first_match['compatibility']:
                comp = first_match['compatibility']
                print("\nCompatibility Report Present:")
                print(f"- Recommendation: {comp['recommendation']}")
                print(f"- Strengths: {len(comp.get('strengths', []))}")
                print(f"- Weaknesses: {len(comp.get('weaknesses', []))}")
                print(f"- Skill Score: {comp['skill_match']['score']}")
                print("SUCCESS: Enhanced matching works.")
            else:
                print("FAILURE: Compatibility report missing in matching-jobs response.")
        else:
            print("No matching jobs found.")

    # 3. Test Direct Compatibility Score
    if parsed_cv_id and job_id:
        print_section("Testing Direct Compatibility Score")
        payload = {"parsed_cv_id": parsed_cv_id, "job_post_id": job_id}
        print(f"POST /compatibility/score with {payload}")
        
        result = make_request(f"{BASE_URL}/compatibility/score", "POST", payload)
        
        if result:
            print("\nDirect Score Result:")
            print(f"Overall: {result['overall_score']}")
            print(f"Rec: {result['recommendation']}")
            print(f"Skills: {result['skill_match']['match_rate']*100}% match")
            print("SUCCESS: Direct scoring works.")
        else:
            print("FAILURE: Direct scoring failed.")
            
        print_section("Testing Batch Scoring")
        batch_payload = {"parsed_cv_id": parsed_cv_id, "job_post_ids": [job_id]}
        print(f"POST /compatibility/batch with {batch_payload}")
        
        batch_results = make_request(f"{BASE_URL}/compatibility/batch", "POST", batch_payload)
        
        if batch_results and isinstance(batch_results, list) and len(batch_results) > 0:
            print(f"Batch returned {len(batch_results)} results.")
            print("SUCCESS: Batch scoring works.")
        else:
            print("FAILURE: Batch scoring failed or empty.")

if __name__ == "__main__":
    main()
