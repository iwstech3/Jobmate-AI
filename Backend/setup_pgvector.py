"""
Setup pgvector extension using Python
"""
import sys
sys.path.insert(0, '.')

from app.database.db import engine
from sqlalchemy import text


def setup_pgvector():
    """Create vector extension in PostgreSQL"""
    print("=" * 50)
    print("Setting up pgvector extension...")
    print("=" * 50)
    
    try:
        with engine.connect() as conn:
            # Check if extension exists
            result = conn.execute(text("""
                SELECT * FROM pg_available_extensions 
                WHERE name = 'vector'
            """))
            
            available = result.fetchone()
            
            if not available:
                print("\n[X] pgvector extension is NOT installed on your PostgreSQL server")
                print("\nYou need to install pgvector first:")
                print("Visit: https://github.com/pgvector/pgvector#installation")
                print("\nOr tell me your OS and I'll give you specific instructions.")
                return False
            
            print("[OK] pgvector extension is available")
            
            # Create extension
            print("\nCreating vector extension...")
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                print("[OK] Vector extension created!")
            except Exception as e:
                print(f"[!] Warning: Could not create extension (might require superuser): {e}")

            # Verify it's enabled
            result = conn.execute(text("""
                SELECT extname, extversion 
                FROM pg_extension 
                WHERE extname = 'vector'
            """))
            
            ext = result.fetchone()
            if ext:
                print(f"[OK] Vector extension enabled! (version: {ext[1]})")
                
                # Test vector type
                conn.execute(text("SELECT '[1,2,3]'::vector"))
                print("[OK] Vector type working!")
                
                print("\n" + "=" * 50)
                print("pgvector setup complete!")
                print("=" * 50)
                return True
            else:
                print("[X] Vector extension not enabled")
                return False
                
    except Exception as e:
        error_msg = str(e)
        print(f"\n[X] Error: {error_msg}")
        
        if "permission denied" in error_msg.lower():
            print("\n[!] Permission error. Try running with postgres superuser:")
            print("   Update DATABASE_URL in .env with superuser credentials")
        elif "does not exist" in error_msg.lower():
            print("\n[!] pgvector is not installed on your PostgreSQL server")
            print("   You need to install it first")
        
        return False


if __name__ == "__main__":
    success = setup_pgvector()
    if not success:
        print("\n📋 Next steps:")
        print("1. Install pgvector on your PostgreSQL server")
        print("2. Run this script again")
        sys.exit(1)