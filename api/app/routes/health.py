"""
Health check routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis
import os

from app.models.schemas import HealthResponse

router = APIRouter()


def get_db():
    """Dependency for database session"""
    from app.main import SessionFactory
    db = SessionFactory()
    try:
        yield db
    finally:
        db.close()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    System health check.

    Checks:
    - Database connectivity
    - Redis connectivity
    - Celery worker status

    Returns:
        Health status of all components
    """
    status = {
        "status": "healthy",
        "database": "unknown",
        "redis": "unknown",
        "worker": "unknown"
    }

    # Check database
    try:
        db.execute(text("SELECT 1"))
        status["database"] = "healthy"
    except Exception as e:
        status["database"] = f"unhealthy: {str(e)}"
        status["status"] = "degraded"

    # Check Redis
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        r.ping()
        status["redis"] = "healthy"
    except Exception as e:
        status["redis"] = f"unhealthy: {str(e)}"
        status["status"] = "degraded"

    # Check Celery worker (simplified)
    try:
        from app.worker import celery_app
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        if stats:
            status["worker"] = f"healthy ({len(stats)} workers)"
        else:
            status["worker"] = "no workers available"
            status["status"] = "degraded"
    except Exception as e:
        status["worker"] = f"unknown: {str(e)}"

    return status
