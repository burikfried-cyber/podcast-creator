"""
Helper script to encode Google Cloud credentials to base64 for Railway deployment
"""
import base64
import sys
import os

print("="*60)
print("GOOGLE CREDENTIALS BASE64 ENCODER")
print("="*60)

# Get credentials file path
creds_file = "C:\\Users\\burik\\podcastCreator2\\podcast-creator-475512-d34ef5fd49b0.json"

if not os.path.exists(creds_file):
    print(f"\n[ERROR] Credentials file not found: {creds_file}")
    print("\nUsage: python encode_credentials.py")
    sys.exit(1)

print(f"\nReading credentials from: {creds_file}")

# Read and encode
try:
    with open(creds_file, 'r') as f:
        content = f.read()
    
    # Encode to base64
    encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    
    print(f"\n[OK] Credentials encoded successfully!")
    print(f"Length: {len(encoded)} characters")
    
    print("\n" + "="*60)
    print("COPY THIS VALUE TO RAILWAY")
    print("="*60)
    print("\n1. Go to Railway dashboard")
    print("2. Go to your service -> Variables")
    print("3. Remove: GOOGLE_APPLICATION_CREDENTIALS")
    print("4. Add new variable:")
    print("   Name: GOOGLE_CREDENTIALS_BASE64")
    print("   Value: (copy the text below)")
    print("\n" + "-"*60)
    print(encoded)
    print("-"*60)
    
    # Also save to file for easy copying
    output_file = "google_credentials_base64.txt"
    with open(output_file, 'w') as f:
        f.write(encoded)
    
    print(f"\n[OK] Also saved to: {output_file}")
    print("\nYou can copy from the file if needed.")
    
except Exception as e:
    print(f"\n[ERROR] Failed to encode: {e}")
    sys.exit(1)
