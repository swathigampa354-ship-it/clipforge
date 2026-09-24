# Test configuration
from fastapi.testclient import TestClient
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from api.app.main import app
from api.core.database import Base, create_tables
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def test_client():
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
async def test_db():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield async_session

    await engine.dispose()


class TestHealth:
    async def test_health_endpoint(self, test_client):
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestAuth:
    async def test_register_endpoint_exists(self, test_client):
        response = test_client.post("/api/v1/auth/register")
        assert response.status_code == 422  # Missing required fields

    async def test_login_endpoint_exists(self, test_client):
        response = test_client.post("/api/v1/auth/login")
        assert response.status_code == 422


class TestProjects:
    async def test_list_projects_requires_auth(self, test_client):
        response = test_client.get("/api/v1/projects")
        assert response.status_code == 401


class TestVideos:
    async def test_upload_requires_auth(self, test_client):
        response = test_client.post("/api/v1/videos/upload")
        assert response.status_code == 401
