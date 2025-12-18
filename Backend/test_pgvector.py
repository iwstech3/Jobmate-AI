"""Test pgvector extension"""
import sys
sys.path.insert(0, '.')

from app.database.db import engine
from sqlalchemy import text

print("Testing pgvector extension...")

try:
    with engine.connect() as conn:
        # Check extension exists
        result = conn.execute(text("""
            SELECT extname, extversion 
            FROM pg_extension 
            WHERE extname = 'vector'
        """))
        
        ext = result.fetchone()
        if ext:
            print(f"✅ pgvector extension enabled (version: {ext[1]})")
        else:
            print("❌ pgvector extension not found")
            sys.exit(1)
        
        # Test vector type
        result = conn.execute(text("SELECT '[1,2,3]'::vector"))
        vec = result.fetchone()[0]
        print(f"✅ Vector type working: {vec}")
        
        print("\n🎉 pgvector is ready!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)