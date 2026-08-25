import os
import sys

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.database import SessionLocal
from app.db.repository import cleanup_orphan_records

def main():
    db = SessionLocal()
    try:
        print("Running orphan records database cleanup...")
        result = cleanup_orphan_records(db)
        print(f"Cleanup finished: {result}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
