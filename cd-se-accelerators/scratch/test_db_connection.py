import sys
import os

# Append project root to system path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import init_db, SessionLocal
from app.db.models import Project

def main():
    print("Testing connection to database...")
    try:
        init_db()
        print("Database tables initialized (or verified).")
        
        # Test querying the database
        db = SessionLocal()
        try:
            projects = db.query(Project).all()
            print(f"Connection successful! Found {len(projects)} projects in the database.")
            for p in projects:
                print(f" - Project: {p.project_name} (ID: {p.id}, Framework: {p.framework})")
        finally:
            db.close()
    except Exception as exc:
        print(f"Database connection failed: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
