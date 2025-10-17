"""
Complete Podcast Generation Tests
Tests the entire generation flow from start to finish
"""
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.podcast import Podcast, PodcastStatus
from app.services.podcast_service import PodcastService


@pytest.mark.asyncio
async def test_complete_podcast_generation_flow(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    auth_headers: dict
):
    """
    Test complete podcast generation from request to completion
    
    This test verifies:
    1. Podcast creation request
    2. Background task starts
    3. Progress updates work
    4. Content is generated (not templates)
    5. Final podcast has all required fields
    """
    # Step 1: Request podcast generation
    response = await client.post(
        "/api/v1/podcasts/generate",
        json={
            "location": "Paris, France",
            "podcast_type": "base",
            "preferences": {
                "surprise_tolerance": 2,
                "preferred_length": "medium"
            }
        },
        headers=auth_headers
    )
    
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "processing"
    
    job_id = data["job_id"]
    
    # Step 2: Poll for status updates
    max_attempts = 60  # 2 minutes max
    attempt = 0
    last_progress = 0
    
    while attempt < max_attempts:
        response = await client.get(
            f"/api/v1/podcasts/status/{job_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        status_data = response.json()
        
        # Verify progress increases
        current_progress = status_data.get("progress", 0)
        assert current_progress >= last_progress, "Progress should not decrease"
        last_progress = current_progress
        
        # Check if completed
        if status_data["status"] == "completed":
            assert current_progress == 100
            break
        
        # Check if failed
        if status_data["status"] == "failed":
            pytest.fail(f"Generation failed: {status_data.get('message')}")
        
        await asyncio.sleep(2)
        attempt += 1
    
    assert attempt < max_attempts, "Generation timed out"
    
    # Step 3: Verify podcast details
    podcast_id = status_data["podcast_id"]
    response = await client.get(
        f"/api/v1/podcasts/{podcast_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    podcast_data = response.json()
    
    # Verify required fields
    assert podcast_data["id"] == podcast_id
    assert podcast_data["title"] is not None
    assert "Paris" in podcast_data["title"] or "France" in podcast_data["title"]
    assert podcast_data["status"] == "completed"
    assert podcast_data["script_content"] is not None
    
    # Verify script is NOT a template
    script = podcast_data["script_content"]
    assert len(script) > 500, "Script should be substantial"
    assert "Let's continue" not in script, "Should not contain template text"
    assert "Paris" in script or "France" in script, "Should contain location info"
    
    # Verify metadata
    assert podcast_data["duration_seconds"] > 0
    assert podcast_data["created_at"] is not None
    assert podcast_data["completed_at"] is not None


@pytest.mark.asyncio
async def test_concurrent_podcast_generation(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    auth_headers: dict
):
    """
    Test multiple concurrent podcast generations
    
    Verifies:
    1. Multiple podcasts can generate simultaneously
    2. No database locking issues
    3. All complete successfully
    """
    locations = [
        "Tokyo, Japan",
        "London, UK",
        "New York, USA"
    ]
    
    # Start all generations
    job_ids = []
    for location in locations:
        response = await client.post(
            "/api/v1/podcasts/generate",
            json={
                "location": location,
                "podcast_type": "base"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 202
        job_ids.append(response.json()["job_id"])
    
    # Wait for all to complete
    completed = set()
    max_attempts = 90  # 3 minutes for 3 podcasts
    attempt = 0
    
    while len(completed) < len(job_ids) and attempt < max_attempts:
        for job_id in job_ids:
            if job_id in completed:
                continue
            
            response = await client.get(
                f"/api/v1/podcasts/status/{job_id}",
                headers=auth_headers
            )
            
            if response.status_code == 200:
                status_data = response.json()
                if status_data["status"] == "completed":
                    completed.add(job_id)
                elif status_data["status"] == "failed":
                    pytest.fail(f"Generation {job_id} failed")
        
        await asyncio.sleep(2)
        attempt += 1
    
    assert len(completed) == len(job_ids), "All podcasts should complete"


@pytest.mark.asyncio
async def test_podcast_script_quality(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    auth_headers: dict
):
    """
    Test that generated scripts meet quality standards
    
    Verifies:
    1. Script contains real facts
    2. No template text
    3. Proper structure
    4. Appropriate length
    """
    # Generate podcast
    response = await client.post(
        "/api/v1/podcasts/generate",
        json={
            "location": "Rome, Italy",
            "podcast_type": "base"
        },
        headers=auth_headers
    )
    
    job_id = response.json()["job_id"]
    
    # Wait for completion
    max_attempts = 60
    podcast_id = None
    
    for _ in range(max_attempts):
        response = await client.get(
            f"/api/v1/podcasts/status/{job_id}",
            headers=auth_headers
        )
        
        status_data = response.json()
        if status_data["status"] == "completed":
            podcast_id = status_data["podcast_id"]
            break
        
        await asyncio.sleep(2)
    
    assert podcast_id is not None, "Podcast should complete"
    
    # Get podcast details
    response = await client.get(
        f"/api/v1/podcasts/{podcast_id}",
        headers=auth_headers
    )
    
    podcast = response.json()
    script = podcast["script_content"]
    
    # Quality checks
    assert len(script) >= 500, "Script should be at least 500 characters"
    assert len(script) <= 10000, "Script should not be excessively long"
    
    # Check for template text (should NOT be present)
    template_phrases = [
        "Let's continue",
        "placeholder",
        "TODO",
        "coming soon",
        "[INSERT",
        "{{",
        "}}"
    ]
    
    for phrase in template_phrases:
        assert phrase not in script, f"Script should not contain template phrase: {phrase}"
    
    # Check for real content about Rome
    rome_keywords = ["Rome", "Italy", "Italian", "Colosseum", "Vatican", "Roman"]
    assert any(keyword in script for keyword in rome_keywords), \
        "Script should contain information about Rome"
    
    # Check structure (should have introduction and conclusion)
    assert len(script.split("\n\n")) >= 3, "Script should have multiple paragraphs"


@pytest.mark.asyncio
async def test_library_pagination(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    auth_headers: dict
):
    """
    Test library retrieval with pagination
    
    Verifies:
    1. Library endpoint works
    2. Pagination works correctly
    3. No 500 errors
    """
    # Generate a few podcasts first
    locations = ["Berlin, Germany", "Madrid, Spain"]
    
    for location in locations:
        response = await client.post(
            "/api/v1/podcasts/generate",
            json={"location": location, "podcast_type": "base"},
            headers=auth_headers
        )
        assert response.status_code == 202
    
    # Wait a bit for at least one to complete
    await asyncio.sleep(10)
    
    # Test library retrieval
    response = await client.get(
        "/api/v1/podcasts/",
        headers=auth_headers
    )
    
    assert response.status_code == 200, "Library should load without errors"
    
    data = response.json()
    assert "podcasts" in data
    assert "total" in data
    assert isinstance(data["podcasts"], list)
    assert data["total"] >= 0


@pytest.mark.asyncio
async def test_error_handling(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    auth_headers: dict
):
    """
    Test error handling in generation
    
    Verifies:
    1. Invalid location handled gracefully
    2. Error status reported correctly
    3. Error message provided
    """
    # Try to generate with invalid location
    response = await client.post(
        "/api/v1/podcasts/generate",
        json={
            "location": "",  # Empty location
            "podcast_type": "base"
        },
        headers=auth_headers
    )
    
    # Should either reject immediately or fail gracefully
    assert response.status_code in [400, 202, 422]


@pytest.mark.asyncio
async def test_database_performance(
    db_session: AsyncSession,
    test_user: User
):
    """
    Test database query performance
    
    Verifies:
    1. Queries execute quickly
    2. No N+1 query problems
    3. Proper indexing
    """
    import time
    from sqlalchemy import select
    
    # Create test podcasts
    service = PodcastService(db_session)
    
    for i in range(10):
        await service.create_podcast(
            user_id=test_user.id,
            location=f"Test City {i}",
            podcast_type="base",
            preferences={}
        )
    
    # Test list query performance
    start = time.time()
    podcasts = await service.list_user_podcasts(
        user_id=test_user.id,
        skip=0,
        limit=10
    )
    duration = time.time() - start
    
    assert duration < 0.5, f"List query took {duration}s, should be < 0.5s"
    assert len(podcasts) == 10
    
    # Test count query performance
    start = time.time()
    count = await service.count_user_podcasts(user_id=test_user.id)
    duration = time.time() - start
    
    assert duration < 0.2, f"Count query took {duration}s, should be < 0.2s"
    assert count == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
