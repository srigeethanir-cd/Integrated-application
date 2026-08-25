import asyncio
import os
from pathlib import Path
import sys

backend_dir = Path(r"D:\Design\Final-BA\Final-BA\backend")
sys.path.insert(0, str(backend_dir))

from app.database.connection import engine
from app.database.migrations import ensure_database_schema

async def main():
    print("Testing DB connection...")
    try:
        await ensure_database_schema(engine)
        print("Success")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
