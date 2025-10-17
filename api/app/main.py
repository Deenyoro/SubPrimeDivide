"""
FastAPI application main entry point
"""
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
import csv
import io

from app.models import get_engine, get_session_factory, init_db
from app.models import Job, JobLog, JobResult, Upload, JobStatus, JobMode
from app.models.schemas import (
    JobCreate, JobResponse, JobControlAction,
    JobLogEntry, JobResultEntry, CSVUploadResponse, HealthResponse
)
from app.routes import jobs, health, equations

# Environment configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://factor:factor_dev_password@localhost:5432/factordb")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# Initialize database
engine = get_engine(DATABASE_URL)
SessionFactory = get_session_factory(engine)
init_db(engine)

# Create FastAPI app
app = FastAPI(
    title="SemiPrime Factor API",
    description="High-performance factorization service with equation-guided search",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs.router, prefix="/api", tags=["jobs"])
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(equations.router, prefix="/api", tags=["equations"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SemiPrime Factor API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )
