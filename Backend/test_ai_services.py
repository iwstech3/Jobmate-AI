"""
Simple test for Gemini AI services
"""
import sys
sys.path.insert(0, '.')  # Add current directory to path

from app.services.ai import get_llm_service, get_embeddings_service


print("Testing LLM Service...")
llm = get_llm_service()
response = llm.generate("Say hello in one sentence")
print(f"✅ LLM Response: {response}\n")

print("Testing Embeddings Service...")
embeddings = get_embeddings_service()
embedding = embeddings.embed_text("Hello world")
print(f"✅ Embedding dimensions: {len(embedding)}")
print(f"✅ First 5 values: {embedding[:5]}\n")

print("🎉 All services working!")