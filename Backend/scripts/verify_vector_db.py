import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Configuration
DATABASE_URL = "postgresql://postgres:Gates123@127.0.0.1:5433/JobMateDB"

def verify_vector_db():
    print("Verifying Vector Database Setup...")
    
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            print("[OK] Database connection successful.")
            
            # Check for vector extension
            result = connection.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
            if result.fetchone():
                print("[OK] 'vector' extension is installed.")
            else:
                print("[FAIL] 'vector' extension is NOT installed.")
                
            # Check for tables
            result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result.fetchall()]
            
            required_tables = ['job_embeddings', 'document_embeddings']
            for table in required_tables:
                if table in tables:
                    print(f"[OK] Table '{table}' exists.")
                else:
                    print(f"[FAIL] Table '{table}' does NOT exist.")

    except OperationalError as e:
        print(f"[FAIL] Could not connect to database: {e}")
    except Exception as e:
        print(f"[FAIL] An error occurred: {e}")

if __name__ == "__main__":
    verify_vector_db()
