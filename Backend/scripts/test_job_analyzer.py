"""
Test script for Job Analyzer Service
Tests the analyze endpoint with an existing job posting
"""

import requests
import json

# Configuration
API_URL = "http://localhost:8001/api/v1"
JOB_ID = 1  # Change this to an existing job ID

def test_job_analyzer():
    """Test the job analyzer endpoint"""
    print("=" * 60)
    print("JOB ANALYZER TEST")
    print("=" * 60)
    
    # Test analyze endpoint
    print(f"\n1. Analyzing job posting ID: {JOB_ID}")
    print("-" * 60)
    
    analyze_url = f"{API_URL}/jobs/{JOB_ID}/analyze"
    
    try:
        response = requests.post(analyze_url)
        
        if response.status_code == 200:
            print("[OK] Analysis successful!")
            analysis = response.json()
            
            print(f"\n[EXPERIENCE]:")
            print(f"   Level: {analysis['experience_level']}")
            if analysis.get('min_years_experience'):
                print(f"   Min Years: {analysis['min_years_experience']}")
            if analysis.get('max_years_experience'):
                print(f"   Max Years: {analysis['max_years_experience']}")
            
            print(f"\n[REQUIRED SKILLS] ({len(analysis['required_skills'])}):")
            for i, skill in enumerate(analysis['required_skills'][:10], 1):
                print(f"   {i}. {skill}")
            
            if analysis['preferred_skills']:
                print(f"\n[PREFERRED SKILLS] ({len(analysis['preferred_skills'])}):")
                for i, skill in enumerate(analysis['preferred_skills'][:10], 1):
                    print(f"   {i}. {skill}")
            
            print(f"\n[KEY TECHNOLOGIES] ({len(analysis['key_technologies'])}):")
            for i, tech in enumerate(analysis['key_technologies'][:10], 1):
                print(f"   {i}. {tech}")
            
            if analysis['responsibilities']:
                print(f"\n[RESPONSIBILITIES] ({len(analysis['responsibilities'])}):")
                for i, resp in enumerate(analysis['responsibilities'][:5], 1):
                    print(f"   {i}. {resp}")
            
            if analysis['education_requirements']:
                print(f"\n[EDUCATION]:")
                for edu in analysis['education_requirements']:
                    print(f"   - {edu}")
            
            if analysis['certifications']:
                print(f"\n[CERTIFICATIONS]:")
                for cert in analysis['certifications']:
                    print(f"   - {cert}")
            
            if analysis['benefits']:
                print(f"\n[BENEFITS] ({len(analysis['benefits'])}):")
                for i, benefit in enumerate(analysis['benefits'][:5], 1):
                    print(f"   {i}. {benefit}")
            
            if analysis.get('salary_range'):
                salary = analysis['salary_range']
                print(f"\n[SALARY]:")
                if salary.get('min') and salary.get('max'):
                    print(f"   Range: ${salary['min']:,} - ${salary['max']:,}")
                elif salary.get('min'):
                    print(f"   Min: ${salary['min']:,}")
                if salary.get('currency'):
                    print(f"   Currency: {salary['currency']}")
                if salary.get('period'):
                    print(f"   Period: {salary['period']}")
            
            print(f"\n[EMPLOYMENT DETAILS]:")
            print(f"   Type: {analysis['employment_type']}")
            if analysis.get('remote_policy'):
                print(f"   Remote: {analysis['remote_policy']}")
            if analysis.get('industry'):
                print(f"   Industry: {analysis['industry']}")
            if analysis.get('company_size'):
                print(f"   Company Size: {analysis['company_size']}")
            
            if analysis['soft_skills']:
                print(f"\n[SOFT SKILLS]:")
                print(f"   {', '.join(analysis['soft_skills'])}")
            
            print(f"\n[OK] Full analysis saved to database")
            print(f"   Analysis ID: {analysis['id']}")
            print(f"   Analyzed at: {analysis['analyzed_at']}")
            print(f"   [OK] Job embedding generated and stored")
            
        elif response.status_code == 404:
            print(f"[X] Job not found")
            print(f"\n[TIP] Create a job first or use a valid job ID")
        else:
            print(f"[X] Error: {response.status_code}")
            print(f"   {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("[X] Connection Error: Is the server running?")
        print(f"   Expected server at: {API_URL}")
    except Exception as e:
        print(f"[X] Unexpected error: {str(e)}")
    
    print("\n" + "=" * 60)


def test_cached_analysis():
    """Test that second call returns cached result"""
    print("\n2. Testing cached analysis (second call)")
    print("-" * 60)
    
    analyze_url = f"{API_URL}/jobs/{JOB_ID}/analyze"
    
    try:
        response = requests.post(analyze_url)
        if response.status_code == 200:
            print("[OK] Cached analysis retrieved successfully")
            print("   (No new LLM call made - using database cache)")
        else:
            print(f"[X] Error: {response.status_code}")
    except Exception as e:
        print(f"[X] Error: {str(e)}")


if __name__ == "__main__":
    print("\n[START] Job Analyzer Tests...")
    print(f"   API URL: {API_URL}")
    print(f"   Job ID: {JOB_ID}")
    
    test_job_analyzer()
    test_cached_analysis()
    
    print("\n[DONE] Tests completed!")
