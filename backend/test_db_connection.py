"""
Test database connection to Supabase PostgreSQL
"""
import asyncio
from sqlalchemy import text
from app.db.base import engine

async def test_connection():
    """Test database connection"""
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("[SUCCESS] Database connection successful!")
            print(f"[SUCCESS] Connected to: {engine.url.database}")
            print(f"[SUCCESS] Host: {engine.url.host}")
            return True
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    exit(0 if success else 1)
