"""
Quick script to check Google Cloud credentials and API status
"""
import os
import sys

print("="*60)
print("GOOGLE CLOUD CREDENTIALS CHECK")
print("="*60)

# Check environment variable
creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
print(f"\n1. Environment Variable:")
print(f"   GOOGLE_APPLICATION_CREDENTIALS = {creds_path}")

if not creds_path:
    print("   [ERROR] Not set!")
    print("\n   Set it with:")
    print('   $env:GOOGLE_APPLICATION_CREDENTIALS="C:\\path\\to\\key.json"')
    sys.exit(1)

# Check file exists
print(f"\n2. File Exists:")
if os.path.exists(creds_path):
    print(f"   [OK] File found: {creds_path}")
    file_size = os.path.getsize(creds_path)
    print(f"   File size: {file_size} bytes")
else:
    print(f"   [ERROR] File not found: {creds_path}")
    sys.exit(1)

# Check file content
print(f"\n3. File Content:")
try:
    import json
    with open(creds_path, 'r') as f:
        creds = json.load(f)
    
    if creds.get('type') == 'service_account':
        print(f"   [OK] Type: Service Account")
        print(f"   Project ID: {creds.get('project_id')}")
        print(f"   Client Email: {creds.get('client_email')}")
    else:
        print(f"   [ERROR] Wrong type: {creds.get('type')}")
        print("   Need 'service_account' credentials")
        sys.exit(1)
except Exception as e:
    print(f"   [ERROR] Cannot read file: {e}")
    sys.exit(1)

# Check Google Cloud library
print(f"\n4. Google Cloud TTS Library:")
try:
    from google.cloud import texttospeech
    print("   [OK] google-cloud-texttospeech installed")
except ImportError:
    print("   [ERROR] Not installed")
    print("   Install with: pip install google-cloud-texttospeech")
    sys.exit(1)

# Try to initialize client
print(f"\n5. Initialize TTS Client:")
try:
    client = texttospeech.TextToSpeechClient()
    print("   [OK] Client initialized successfully")
except Exception as e:
    print(f"   [ERROR] Client initialization failed:")
    print(f"   {str(e)}")
    
    if "403" in str(e):
        print("\n   This is a PERMISSIONS error. To fix:")
        print("   1. Go to: https://console.cloud.google.com/apis/library/texttospeech.googleapis.com")
        print(f"   2. Select project: {creds.get('project_id')}")
        print("   3. Click 'ENABLE' button")
        print("   4. Wait 1-2 minutes for it to propagate")
        print("   5. Run this script again")
    sys.exit(1)

# Try a simple API call
print(f"\n6. Test API Call:")
try:
    # List available voices (simple API call)
    voices = client.list_voices()
    voice_count = len(voices.voices)
    print(f"   [OK] API is working!")
    print(f"   Available voices: {voice_count}")
    
    # Show a few English voices
    en_voices = [v for v in voices.voices if v.language_codes[0].startswith('en-US')][:3]
    print(f"   Sample voices:")
    for v in en_voices:
        print(f"     - {v.name}")
    
except Exception as e:
    print(f"   [ERROR] API call failed:")
    print(f"   {str(e)}")
    sys.exit(1)

print("\n" + "="*60)
print("ALL CHECKS PASSED!")
print("="*60)
print("\nYour Google Cloud TTS is configured correctly!")
print("You can now run: python test_audio_generation.py")
