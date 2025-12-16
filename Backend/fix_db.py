from app.database.db import engine
from sqlalchemy import text

def fix_db():
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS job_views CASCADE"))
        conn.commit()
        print("Dropped job_views table.")

if __name__ == "__main__":
    fix_db()
