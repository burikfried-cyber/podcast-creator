"""
Simple Log Viewer
View the latest podcast generation logs in a readable format
"""
from pathlib import Path
import sys

def view_latest_log():
    """View the most recent log file"""
    log_dir = Path("logs")
    
    if not log_dir.exists():
        print("❌ No logs directory found")
        return
    
    # Find latest log file
    log_files = sorted(
        log_dir.glob("podcast_generation_*.log"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    if not log_files:
        print("❌ No log files found")
        return
    
    latest_log = log_files[0]
    print(f"📝 Viewing: {latest_log.name}")
    print("=" * 80)
    print()
    
    try:
        with open(latest_log, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Highlight important sections
            for line in content.split('\n'):
                if 'ERROR' in line or 'FAILED' in line:
                    print(f"🔴 {line}")
                elif 'SUCCESS' in line or 'DONE' in line:
                    print(f"✅ {line}")
                elif 'STEP' in line:
                    print(f"📍 {line}")
                elif '===' in line:
                    print(f"\n{'='*80}")
                    print(f"{'='*80}\n")
                else:
                    print(line)
    
    except Exception as e:
        print(f"❌ Error reading log: {e}")

if __name__ == "__main__":
    view_latest_log()
