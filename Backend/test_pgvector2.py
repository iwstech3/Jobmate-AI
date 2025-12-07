"""Test pgvector with fresh connection"""
import psycopg2

print("Testing pgvector with direct connection...")

try:
    # Direct connection (bypass SQLAlchemy)
    conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="JobMateDB",
    user="postgres",
    password="Gates123"
)

    cur = conn.cursor()
    
    # Check extension
    cur.execute("""
        SELECT extname, extversion 
        FROM pg_extension 
        WHERE extname = 'vector'
    """)
    
    result = cur.fetchone()
    if result:
        print(f"[OK] pgvector found: {result[0]} version {result[1]}")
    else:
        print("[X] pgvector not found")
    
    # Test vector type
    cur.execute("SELECT '[1,2,3]'::vector")
    vec = cur.fetchone()[0]
    print(f"[OK] Vector type works: {vec}")
    
    cur.close()
    conn.close()
    
    print("\npgvector is ready!")
    
except Exception as e:
    print(f"[X] Error: {e}")