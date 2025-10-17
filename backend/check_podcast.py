import asyncio
import httpx

async def check():
    async with httpx.AsyncClient() as client:
        # Login
        r = await client.post('http://127.0.0.1:8000/api/v1/auth/login', 
                             json={'email': 'test@example.com', 'password': 'TestPassword123'})
        token = r.json()['access_token']
        
        # Get podcast
        r2 = await client.get('http://127.0.0.1:8000/api/v1/podcasts/fa3421d6-a957-4c03-acfe-dd803155e18b',
                             headers={'Authorization': f'Bearer {token}'})
        podcast = r2.json()
        
        print('TITLE:', podcast['title'])
        print('SCRIPT LENGTH:', len(podcast['script_content']))
        print('\nSCRIPT CONTENT:')
        print(podcast['script_content'])

asyncio.run(check())
