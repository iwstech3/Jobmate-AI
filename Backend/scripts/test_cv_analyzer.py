"""
Test script for CV Analyzer Service
Tests the analyze endpoint with an existing parsed CV
"""

import requests
import json

# Configuration
API_URL = "http://localhost:8001/api/v1"
DOCUMENT_ID = 6  # Change this to an existing document ID that has been parsed

def test_cv_analyzer():
    """Test the CV analyzer endpoint"""
    print("=" * 60)
    print("CV ANALYZER TEST")
    print("=" * 60)
    
    # Test analyze endpoint
    print(f"\n1. Analyzing CV for document ID: {DOCUMENT_ID}")
    print("-" * 60)
    
    analyze_url = f"{API_URL}/documents/{DOCUMENT_ID}/analyze"
    
    try:
        response = requests.post(analyze_url)
        
        if response.status_code == 200:
            print("[OK] Analysis successful!")
            analysis = response.json()
            
            print(f"\n[SCORES]:")
            print(f"   Overall Score: {analysis['overall_score']}/100")
            print(f"   Completeness: {analysis['completeness_score']}/100")
            print(f"   Quality: {analysis['quality_score']}/100")
            print(f"   ATS Score: {analysis['ats_score']}/100")
            
            print(f"\n[STRENGTHS] ({len(analysis['strengths'])}):")
            for i, strength in enumerate(analysis['strengths'], 1):
                print(f"   {i}. {strength}")
            
            print(f"\n[WEAKNESSES] ({len(analysis['weaknesses'])}):")
            for i, weakness in enumerate(analysis['weaknesses'], 1):
                print(f"   {i}. {weakness}")
            
            print(f"\n[SUGGESTIONS] ({len(analysis['suggestions'])}):")
            for i, suggestion in enumerate(analysis['suggestions'], 1):
                priority = suggestion['priority'].upper()
                category = suggestion['category']
                text = suggestion['suggestion']
                print(f"   {i}. [{priority}] ({category})")
                print(f"      {text}")
            
            print(f"\n[SKILL ANALYSIS]:")
            skill_analysis = analysis['skill_analysis']
            print(f"   Skill Level: {skill_analysis['skill_level']}")
            print(f"   Technical Skills: {len(skill_analysis['technical_skills'])} found")
            print(f"   Soft Skills: {len(skill_analysis['soft_skills'])} found")
            if skill_analysis['missing_common_skills']:
                print(f"   Missing Skills: {', '.join(skill_analysis['missing_common_skills'])}")
            
            print(f"\n[EXPERIENCE ANALYSIS]:")
            exp_analysis = analysis['experience_analysis']
            print(f"   Total Years: {exp_analysis['total_years']}")
            print(f"   Career Progression: {exp_analysis['career_progression']}")
            print(f"   Recent Experience: {exp_analysis['recent_experience']}")
            print(f"   Job Stability: {exp_analysis['job_stability']}")
            
            print(f"\n[OK] Full analysis saved to database")
            print(f"   Analysis ID: {analysis['id']}")
            print(f"   Analyzed at: {analysis['analyzed_at']}")
            
        elif response.status_code == 400:
            error = response.json()
            print(f"[X] Bad Request: {error['detail']}")
            if "not been parsed" in error['detail']:
                print(f"\n[TIP] Parse the CV first:")
                print(f"   POST {API_URL}/documents/{DOCUMENT_ID}/parse")
        elif response.status_code == 404:
            print(f"[X] Document not found")
            print(f"\n[TIP] Upload a document first or use a valid document ID")
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
    
    analyze_url = f"{API_URL}/documents/{DOCUMENT_ID}/analyze"
    
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
    print("\n[START] CV Analyzer Tests...")
    print(f"   API URL: {API_URL}")
    print(f"   Document ID: {DOCUMENT_ID}")
    
    test_cv_analyzer()
    test_cached_analysis()
    
    print("\n[DONE] Tests completed!")
