import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

print("Starting database test...")

# Load .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

print("DATABASE_URL:")
print(DATABASE_URL)

if not DATABASE_URL:
    raise Exception("DATABASE_URL not found in .env")

try:
    engine = create_engine(DATABASE_URL)


    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))

        print("\n✅ Successfully Connected to Neon PostgreSQL!\n")
        print(result.scalar())


except Exception as e:
    print("\n❌ Connection Failed\n")
    print(e)
