"""
Pytest configuration and global mocks.
"""
import os

# Force tests to use an in-memory SQLite database and test environment variables
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["ENVIRONMENT"] = "testing"

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

# Register models in SQLAlchemy metadata
from app.models import user, memory, task, conversation, calendar_event, email # noqa: F401

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_db():
    """Mock AsyncSession for database interactions."""
    db = AsyncMock()
    # Mock database query executions
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.close = AsyncMock()
    return db

@pytest.fixture
def mock_redis(monkeypatch):
    """Mock Redis client."""
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=1)
    client.ping = AsyncMock(return_value=True)
    monkeypatch.setattr("app.redis_client.redis_client", client)
    monkeypatch.setattr("app.redis_client.get_redis", AsyncMock(return_value=client))
    return client

@pytest.fixture(autouse=True)
def override_settings(monkeypatch):
    """Override configuration to use dummy values for testing."""
    monkeypatch.setattr("app.config.settings.openai_api_key", "mock-key")
    monkeypatch.setattr("app.config.settings.tavily_api_key", "mock-key")
    monkeypatch.setattr("app.config.settings.secret_key", "test-secret-key-at-least-32-chars-long-12345")
    monkeypatch.setattr("app.config.settings.environment", "testing")

@pytest.fixture
async def client(mock_db, mock_redis, monkeypatch):
    """Async test client for API integration tests."""
    # Mock Redis client helper to return our mock
    monkeypatch.setattr("app.redis_client.get_redis", AsyncMock(return_value=mock_redis))
    
    # Mock get_db dependency
    from app.database import get_db
    from app.main import app

    async def _get_db_override():
        yield mock_db

    app.dependency_overrides[get_db] = _get_db_override
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
        
    app.dependency_overrides.clear()

@pytest.fixture
async def authenticated_client(client, mock_db):
    """Client with pre-authenticated user session."""
    import uuid
    from app.models.user import User
    from app.api.auth import get_current_user
    from app.main import app

    test_user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        username="testuser",
        full_name="Test User",
        is_active=True,
        profile={"voice": "alloy"}
    )

    async def _get_current_user_override():
        return test_user

    app.dependency_overrides[get_current_user] = _get_current_user_override
    yield client
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]

