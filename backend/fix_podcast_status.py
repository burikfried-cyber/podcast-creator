"""
Quick script to fix podcast status casing in database
Converts COMPLETED -> completed, FAILED -> failed, etc.
"""
import asyncio
import sqlite3
from pathlib import Path

async def fix_status_casing():
    """Fix status casing in the database"""
    db_path = Path("podcast_generator.db")
    
    if not db_path.exists():
        print("❌ Database not found")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Update all status values to lowercase
        cursor.execute("UPDATE podcasts SET status = LOWER(status)")
        affected = cursor.rowcount
        conn.commit()
        
        print(f"✅ Fixed {affected} podcast status values")
        
        # Show current statuses
        cursor.execute("SELECT status, COUNT(*) FROM podcasts GROUP BY status")
        results = cursor.fetchall()
        
        print("\n📊 Current status distribution:")
        for status, count in results:
            print(f"  - {status}: {count}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    asyncio.run(fix_status_casing())
