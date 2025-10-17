import asyncio
import httpx

async def test_library():
    async with httpx.AsyncClient() as client:
        # Login
        r = await client.post('http://127.0.0.1:8000/api/v1/auth/login', 
                             json={'email': 'test@example.com', 'password': 'TestPassword123'})
        token = r.json()['access_token']
        
        # Get library
        r2 = await client.get('http://127.0.0.1:8000/api/v1/podcasts/',
                             headers={'Authorization': f'Bearer {token}'})
        
        print(f"Status Code: {r2.status_code}")
        if r2.status_code == 200:
            library = r2.json()
            print(f"\n[SUCCESS] Library loaded!")
            print(f"Total podcasts: {library['total']}")
            print(f"Podcasts returned: {len(library['podcasts'])}")
            print(f"\nPodcasts:")
            for p in library['podcasts']:
                print(f"  - {p['title']} ({p['status']})")
        else:
            print(f"\n[ERROR] {r2.text}")

asyncio.run(test_library())
