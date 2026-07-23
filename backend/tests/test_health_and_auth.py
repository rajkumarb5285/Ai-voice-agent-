"""
Unit tests for Health check and Authentication endpoints.
"""
import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from app.models.user import User

@pytest.mark.asyncio
async def test_health_check(client):
    """Verify health check endpoint returns 200 and correct status metadata."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["environment"] == "testing"

@pytest.mark.asyncio
async def test_auth_register(client, mock_db):
    """Verify register route creates user and returns user info."""
    # Mock user query to return None (user doesn't exist yet) using a sync MagicMock result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    # Mock db.refresh to set id and created_at on the user instance
    async def mock_refresh(instance, *args, **kwargs):
        instance.id = uuid.uuid4()
        instance.created_at = datetime.utcnow()
    mock_db.refresh.side_effect = mock_refresh

    reg_payload = {
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "strongpassword123",
        "full_name": "Test User"
    }

    response = await client.post("/api/auth/register", json=reg_payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "testuser@example.com"
    assert data["user"]["username"] == "testuser"
    assert "id" in data["user"]

@pytest.mark.asyncio
async def test_auth_login(client, mock_db):
    """Verify login route validates password and returns JWT token."""
    # Setup mock user with id and created_at
    from app.services.auth_service import get_password_hash
    hashed = get_password_hash("strongpassword123")
    
    mock_user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        username="testuser",
        hashed_password=hashed,
        created_at=datetime.utcnow()
    )
    
    # Mock query lookup for username/email using a sync MagicMock result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute.return_value = mock_result

    login_payload = {
        "email": "testuser@example.com",
        "password": "strongpassword123"
    }

    response = await client.post("/api/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "testuser@example.com"
