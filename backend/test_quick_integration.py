"""
Quick Integration Test
Tests the complete flow without pytest framework
"""
import asyncio
import httpx
from app.core.security import security

BASE_URL = "http://127.0.0.1:8000/api/v1"

async def test_complete_flow():
    """Test complete podcast generation flow"""
    print("\n" + "="*60)
    print("QUICK INTEGRATION TEST")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Step 1: Register user
        print("\n[1/6] Registering test user...")
        try:
            response = await client.post(
                f"{BASE_URL}/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "TestPassword123"
                }
            )
            if response.status_code == 201:
                print("[SUCCESS] User registered")
            elif response.status_code == 400:
                print("[INFO] User already exists, continuing...")
            else:
                print(f"[ERROR] Registration failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"[ERROR] Registration error: {e}")
            return False
        
        # Step 2: Login
        print("\n[2/6] Logging in...")
        try:
            response = await client.post(
                f"{BASE_URL}/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "TestPassword123"
                }
            )
            if response.status_code != 200:
                print(f"[ERROR] Login failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            tokens = response.json()
            access_token = tokens["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
            print("[SUCCESS] Logged in successfully")
        except Exception as e:
            print(f"[ERROR] Login error: {e}")
            return False
        
        # Step 3: Generate podcast
        print("\n[3/6] Starting podcast generation...")
        try:
            response = await client.post(
                f"{BASE_URL}/podcasts/generate",
                json={
                    "location": "Paris, France",
                    "podcast_type": "base",
                    "preferences": {
                        "surprise_tolerance": 2,
                        "preferred_length": "medium"
                    }
                },
                headers=headers
            )
            if response.status_code != 202:
                print(f"[ERROR] Generation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            data = response.json()
            job_id = data["job_id"]
            print(f"[SUCCESS] Generation started (Job ID: {job_id})")
        except Exception as e:
            print(f"[ERROR] Generation error: {e}")
            return False
        
        # Step 4: Poll for completion
        print("\n[4/6] Waiting for generation to complete...")
        max_attempts = 60  # 2 minutes
        completed = False
        
        for attempt in range(max_attempts):
            try:
                response = await client.get(
                    f"{BASE_URL}/podcasts/status/{job_id}",
                    headers=headers
                )
                
                if response.status_code != 200:
                    print(f"[ERROR] Status check failed: {response.status_code}")
                    await asyncio.sleep(2)
                    continue
                
                status_data = response.json()
                status = status_data["status"]
                progress = status_data.get("progress", 0)
                
                print(f"[INFO] Progress: {progress}% | Status: {status}")
                
                if status == "completed":
                    completed = True
                    podcast_id = status_data["podcast_id"]
                    print(f"[SUCCESS] Generation completed! (Podcast ID: {podcast_id})")
                    break
                elif status == "failed":
                    print(f"[ERROR] Generation failed: {status_data.get('message')}")
                    return False
                
                await asyncio.sleep(2)
            except Exception as e:
                print(f"[ERROR] Status check error: {e}")
                await asyncio.sleep(2)
        
        if not completed:
            print("[ERROR] Generation timed out")
            return False
        
        # Step 5: Verify podcast details
        print("\n[5/6] Verifying podcast details...")
        try:
            response = await client.get(
                f"{BASE_URL}/podcasts/{podcast_id}",
                headers=headers
            )
            
            if response.status_code != 200:
                print(f"[ERROR] Failed to get podcast: {response.status_code}")
                return False
            
            podcast = response.json()
            
            # Verify required fields
            assert podcast["title"] is not None, "Title missing"
            assert "Paris" in podcast["title"] or "France" in podcast["title"], "Title doesn't mention location"
            assert podcast["script_content"] is not None, "Script missing"
            assert len(podcast["script_content"]) > 200, "Script too short"
            
            # Check for actual template text (not natural language)
            template_markers = ["Let's continue with", "TODO", "placeholder", "{{", "}}"]
            for marker in template_markers:
                assert marker not in podcast["script_content"], f"Template marker found: {marker}"
            
            print(f"[SUCCESS] Podcast verified:")
            print(f"  - Title: {podcast['title']}")
            print(f"  - Script length: {len(podcast['script_content'])} characters")
            print(f"  - Duration: {podcast['duration_seconds']} seconds")
        except AssertionError as e:
            print(f"[ERROR] Verification failed: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] Verification error: {e}")
            return False
        
        # Step 6: Test library
        print("\n[6/6] Testing library endpoint...")
        try:
            response = await client.get(
                f"{BASE_URL}/podcasts/",
                headers=headers
            )
            
            if response.status_code != 200:
                print(f"[ERROR] Library failed: {response.status_code}")
                return False
            
            library = response.json()
            assert "podcasts" in library, "Podcasts list missing"
            assert library["total"] > 0, "No podcasts in library"
            
            print(f"[SUCCESS] Library loaded:")
            print(f"  - Total podcasts: {library['total']}")
            print(f"  - Podcasts returned: {len(library['podcasts'])}")
        except Exception as e:
            print(f"[ERROR] Library error: {e}")
            return False
    
    print("\n" + "="*60)
    print("[SUCCESS] ALL TESTS PASSED!")
    print("="*60)
    return True

if __name__ == "__main__":
    success = asyncio.run(test_complete_flow())
    exit(0 if success else 1)
