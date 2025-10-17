"""
Pytest configuration and shared fixtures for SemiPrime Factor tests.
"""

import os
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient

# Import your app components
from app.main import app
from app.database import Base, get_db
from app.models.database import Job, JobLog, JobResult, Upload


# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://factor:factor_test_pass@localhost:5432/factordb_test"
)

TEST_DATABASE_URL_ASYNC = TEST_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL_ASYNC,
        echo=False,
        future=True
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """Create a test client with overridden database dependency."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_semiprime():
    """Provide a sample semiprime for testing."""
    return {
        "small": 143,  # 11 * 13
        "medium": 323,  # 17 * 19
        "large": 2021,  # 43 * 47
        "rsa_100": 1522605027922533360535618378132637429718068114961380688657908494580122963258952897654000350692006139  # RSA-100
    }


@pytest.fixture
def sample_job_data():
    """Provide sample job creation data."""
    return {
        "n": "143",
        "mode": "fully_factor",
        "algorithm_policy": {
            "use_trial_division": True,
            "trial_division_limit": 10000000,
            "use_pollard_rho": True,
            "pollard_rho_iterations": 1000000,
            "use_ecm": False,
            "use_equation": False
        }
    }


@pytest.fixture
def redis_client():
    """Create a Redis client for testing."""
    import redis
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    client = redis.from_url(redis_url)

    yield client

    # Cleanup
    client.flushdb()
    client.close()


@pytest.fixture
def celery_app():
    """Create a Celery app for testing."""
    from app.worker import celery_app
    return celery_app


# Markers for easy test filtering
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
