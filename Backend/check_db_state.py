from sqlalchemy import create_engine, inspect
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fallback to default if env not loaded properly, though it should be.
    # Try to read from .env file manually if needed, but python-dotenv should work.
    # Assuming standard project structure or user can fix it.
    print("DATABASE_URL not found in env.")
    exit(1)

try:
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("Existing tables:", tables)
    
    if "applications" in tables:
        print("Table 'applications' EXISTS.")
    else:
        print("Table 'applications' DOES NOT EXIST.")
        
except Exception as e:
    print(f"Error checking database: {e}")
