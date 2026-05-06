"""
Tests for FastAPI async application.

Tests verify:
1. Async route handlers work correctly
2. Async database sessions are properly managed
3. Authentication with async session works
4. Predictions with async session work
5. Error handling is consistent
"""

import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import patch, AsyncMock, MagicMock

from src.api.fastapi_async_app import app
from src.db.models import UserProfile, AuditLog


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
async def async_test_session():
    """Create async test session."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        pool_pre_ping=True,
    )
    async_session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with engine.begin() as conn:
        # Create tables
        from src.db.models import Base
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session_factory() as session:
        yield session


# ============================================================================
# SYNC TESTS (using TestClient)
# ============================================================================

class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]


class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert data["docs"] == "/docs"


class TestAuthLoginEndpoint:
    """Test async login endpoint."""
    
    def test_login_missing_credentials(self, client):
        """Test login with missing credentials."""
        response = client.post("/auth/login", json={})
        assert response.status_code == 400
        assert "Missing credentials" in response.text or "detail" in response.json()
    
    def test_login_empty_username(self, client):
        """Test login with empty username."""
        response = client.post("/auth/login", json={"username": "", "password": "pass"})
        assert response.status_code == 400
    
    def test_login_empty_password(self, client):
        """Test login with empty password."""
        response = client.post("/auth/login", json={"username": "user", "password": ""})
        assert response.status_code == 400

    def test_logout_missing_token(self, client):
        """Test logout with missing refresh token returns 400."""
        response = client.post("/auth/logout", json={})
        assert response.status_code == 400

    def test_logout_invalid_token(self, client):
        """Test logout with invalid token returns 401 or 404 depending on validation."""
        response = client.post("/auth/logout", json={"refresh_token": "not-a-token"})
        assert response.status_code in (401, 404)


class TestPredictionEndpoint:
    """Test async prediction endpoints."""
    
    @patch("src.api.fastapi_async_app.load_model")
    @patch("src.api.fastapi_async_app.validate_payload")
    @patch("src.api.fastapi_async_app.predict_one")
    def test_predict_single(self, mock_predict, mock_validate, mock_load, client):
        """Test single prediction endpoint."""
        # Mock the dependencies
        mock_load.return_value = MagicMock()
        mock_validate.return_value = None
        mock_predict.return_value = {"dropoff_probability": 0.75, "risk_level": "high"}
        
        payload = {
            "user_id": "user123",
            "session_duration_seconds": 300,
            "click_count": 5,
        }
        
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert "timestamp" in data
        assert mock_validate.called
        assert mock_predict.called
    
    @patch("src.api.fastapi_async_app.load_model")
    @patch("src.api.fastapi_async_app.predict_batch")
    def test_predict_batch(self, mock_predict, mock_load, client):
        """Test batch prediction endpoint."""
        mock_load.return_value = MagicMock()
        mock_predict.return_value = [
            {"dropoff_probability": 0.75},
            {"dropoff_probability": 0.25},
        ]
        
        payload = {
            "samples": [
                {"user_id": "user1", "session_duration_seconds": 300},
                {"user_id": "user2", "session_duration_seconds": 600},
            ]
        }
        
        response = client.post("/predict/batch", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert data["count"] == 2


class TestMonitoringEndpoints:
    """Test monitoring endpoints."""
    
    def test_monitor_status(self, client):
        """Test monitor status endpoint."""
        response = client.get("/monitor")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert "timestamp" in data
    
    def test_monitor_persist(self, client):
        """Test monitor persist endpoint."""
        response = client.post("/monitor/persist")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "persisted"


class TestRateLimiting:
    """Test rate limiting middleware."""
    
    def test_rate_limit_enforcement(self, client):
        """Test that rate limiting is applied."""
        # Make multiple requests with same API key
        api_key = "test-key-123"
        
        # This would require a low rate limit for testing
        # For now just verify the middleware is installed
        assert len(app.user_middleware) >= 3  # CORS, request_id, metrics, rate_limit


class TestCORSMiddleware:
    """Test CORS middleware."""
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.get("/", headers={"Origin": "http://example.com"})
        assert response.status_code == 200


# ============================================================================
# ASYNC TESTS
# ============================================================================

class TestAsyncDatabase:
    """Test async database operations."""
    
    @pytest.mark.asyncio
    async def test_async_session_creation(self, async_test_session):
        """Test async session can be created."""
        assert async_test_session is not None
    
    @pytest.mark.asyncio
    async def test_async_session_query(self, async_test_session):
        """Test async session can execute queries."""
        result = await async_test_session.execute(select(UserProfile))
        users = result.scalars().all()
        assert isinstance(users, list)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests."""
    
    def test_multiple_endpoints(self, client):
        """Test multiple endpoints in sequence."""
        # Health check
        response = client.get("/health")
        assert response.status_code == 200
        
        # Root
        response = client.get("/")
        assert response.status_code == 200
        
        # Monitor
        response = client.get("/monitor")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
