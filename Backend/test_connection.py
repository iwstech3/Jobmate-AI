"""Test database connection"""
import sys
sys.path.insert(0, '.')

from app.database.db import engine
from sqlalchemy import text

print("Testing database connection...")

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"[OK] Connected successfully!")
        print(f"   PostgreSQL version: {version[:80]}")
except Exception as e:
    print(f"[X] Connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Check docker-compose ps - container running?")
    print("2. Check .env - DATABASE_URL correct?")
    print("3. Check password matches docker-compose.yml")
    sys.exit(1)