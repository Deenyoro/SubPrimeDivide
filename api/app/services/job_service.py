"""
Job service for business logic
"""
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.models import Job, JobLog, JobResult, JobStatus, JobMode
from app.models.schemas import JobCreate
from app.worker import run_factorization_task


class JobService:
    """Service for managing factorization jobs"""

    def __init__(self, db: Session):
        self.db = db

    def create_job(self, job_data: JobCreate) -> Job:
        """
        Create a new factorization job and enqueue it.

        Args:
            job_data: Job configuration

        Returns:
            Created job
        """
        # Generate job ID
        job_id = str(uuid.uuid4())

        # Create job record
        job = Job(
            id=job_id,
            n=job_data.n,
            mode=JobMode(job_data.mode.value),
            lower_bound=job_data.lower_bound,
            upper_bound=job_data.upper_bound,
            equation_config=job_data.equation_config or {},
            algorithm_policy=job_data.algorithm_policy.dict() if job_data.algorithm_policy else {},
            ecm_params=job_data.ecm_params.dict() if job_data.ecm_params else {},
            use_equation=job_data.use_equation,
            status=JobStatus.PENDING
        )

        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        # Log job creation
        self._add_log(job_id, "INFO", "Job created", "initialization")

        # Enqueue Celery task
        run_factorization_task.delay(job_id)

        return job

    def pause_job(self, job_id: str) -> Job:
        """Pause a running job"""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError("Job not found")

        if job.status == JobStatus.RUNNING:
            job.status = JobStatus.PAUSED
            self._add_log(job_id, "INFO", "Job paused by user", "control")
            self.db.commit()

        return job

    def resume_job(self, job_id: str) -> Job:
        """Resume a paused job"""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError("Job not found")

        if job.status == JobStatus.PAUSED:
            job.status = JobStatus.RUNNING
            self._add_log(job_id, "INFO", "Job resumed by user", "control")
            self.db.commit()
            # Re-enqueue task
            run_factorization_task.delay(job_id)

        return job

    def cancel_job(self, job_id: str) -> Job:
        """Cancel a job"""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError("Job not found")

        if job.status in [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.PAUSED]:
            job.status = JobStatus.CANCELLED
            job.finished_at = datetime.utcnow()
            self._add_log(job_id, "INFO", "Job cancelled by user", "control")
            self.db.commit()

        return job

    def _add_log(self, job_id: str, level: str, message: str, stage: str = None, payload: dict = None):
        """Add a log entry"""
        log = JobLog(
            job_id=job_id,
            level=level,
            message=message,
            stage=stage,
            payload=payload
        )
        self.db.add(log)
        self.db.commit()
