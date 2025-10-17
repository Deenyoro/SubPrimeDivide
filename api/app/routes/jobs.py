"""
Job management routes
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
import uuid
import csv
import io
import os
import json

from app.models import Job, JobLog, JobResult, Upload, JobStatus
from app.models.schemas import (
    JobCreate, JobResponse, JobControlAction,
    JobLogEntry, JobResultEntry, CSVUploadResponse
)
from app.services.job_service import JobService

router = APIRouter()


def get_db():
    """Dependency for database session"""
    from app.main import SessionFactory
    db = SessionFactory()
    try:
        yield db
    finally:
        db.close()


@router.post("/jobs", response_model=JobResponse)
async def create_job(job_data: JobCreate, db: Session = Depends(get_db)):
    """
    Create a new factorization job.

    Args:
        job_data: Job configuration
        db: Database session

    Returns:
        Created job details
    """
    service = JobService(db)
    job = service.create_job(job_data)
    return job


@router.get("/jobs", response_model=List[JobResponse])
async def list_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    List all jobs with pagination.

    Args:
        skip: Number of records to skip
        limit: Maximum records to return
        db: Database session

    Returns:
        List of jobs
    """
    jobs = db.query(Job).order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
    return jobs


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """
    Get job details by ID.

    Args:
        job_id: Job UUID
        db: Database session

    Returns:
        Job details
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/jobs/{job_id}/control")
async def control_job(job_id: str, action: JobControlAction, db: Session = Depends(get_db)):
    """
    Control job execution (pause, resume, cancel).

    Args:
        job_id: Job UUID
        action: Control action
        db: Database session

    Returns:
        Updated job status
    """
    service = JobService(db)

    if action.action == "pause":
        job = service.pause_job(job_id)
    elif action.action == "resume":
        job = service.resume_job(job_id)
    elif action.action == "cancel":
        job = service.cancel_job(job_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    return {"status": "success", "job_status": job.status}


@router.get("/jobs/{job_id}/logs", response_model=List[JobLogEntry])
async def get_job_logs(
    job_id: str,
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    """
    Get job execution logs.

    Args:
        job_id: Job UUID
        skip: Number of records to skip
        limit: Maximum records to return
        db: Database session

    Returns:
        List of log entries
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    logs = db.query(JobLog).filter(
        JobLog.job_id == job_id
    ).order_by(JobLog.timestamp.desc()).offset(skip).limit(limit).all()

    return logs


@router.get("/jobs/{job_id}/results", response_model=List[JobResultEntry])
async def get_job_results(job_id: str, db: Session = Depends(get_db)):
    """
    Get factorization results for a job.

    Args:
        job_id: Job UUID
        db: Database session

    Returns:
        List of factors found
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    results = db.query(JobResult).filter(JobResult.job_id == job_id).all()
    return results


@router.websocket("/jobs/{job_id}/stream")
async def stream_job_logs(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time job logs and progress.

    Args:
        websocket: WebSocket connection
        job_id: Job UUID
    """
    await websocket.accept()

    try:
        # Get database session
        from app.main import SessionFactory
        db = SessionFactory()

        # Verify job exists
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            await websocket.send_json({"error": "Job not found"})
            await websocket.close()
            return

        # Stream logs and progress
        last_log_id = 0

        while True:
            # Refresh job status
            db.refresh(job)

            # Get new logs
            new_logs = db.query(JobLog).filter(
                JobLog.job_id == job_id,
                JobLog.id > last_log_id
            ).order_by(JobLog.id).all()

            for log in new_logs:
                await websocket.send_json({
                    "type": "log",
                    "timestamp": log.timestamp.isoformat(),
                    "level": log.level,
                    "message": log.message,
                    "stage": log.stage,
                    "payload": log.payload
                })
                last_log_id = log.id

            # Send progress update
            await websocket.send_json({
                "type": "progress",
                "status": job.status.value,
                "progress_percent": job.progress_percent,
                "current_candidate": job.current_candidate
            })

            # Exit if job is complete
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                await websocket.send_json({"type": "complete", "status": job.status.value})
                break

            # Wait before next update
            import asyncio
            await asyncio.sleep(1)

        db.close()

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


@router.post("/upload/csv", response_model=CSVUploadResponse)
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a CSV file with numbers to factor.

    Expected format: Each row contains one number, or columns: number, lower_bound, upper_bound

    Args:
        file: Uploaded CSV file
        db: Database session

    Returns:
        Upload token for use in job creation
    """
    # Generate token
    token = str(uuid.uuid4())

    # Create uploads directory
    upload_dir = "/app/uploads"
    os.makedirs(upload_dir, exist_ok=True)

    # Save file
    file_path = os.path.join(upload_dir, f"{token}.csv")

    # Read and validate CSV
    content = await file.read()
    text_content = content.decode('utf-8')

    # Count rows
    reader = csv.reader(io.StringIO(text_content))
    rows = list(reader)
    row_count = len([r for r in rows if r])  # Non-empty rows

    if row_count == 0:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    # Save to disk
    with open(file_path, 'w') as f:
        f.write(text_content)

    # Store upload record
    upload = Upload(
        token=token,
        filename=file.filename,
        path=file_path,
        rows=row_count,
        status="uploaded"
    )
    db.add(upload)
    db.commit()

    return CSVUploadResponse(
        token=token,
        filename=file.filename,
        rows=row_count
    )
