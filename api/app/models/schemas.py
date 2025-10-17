"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class JobModeEnum(str, Enum):
    RANGE_SCAN = "range_scan"
    CSV_INPUT = "csv_input"
    EQUATION_GUIDED = "equation_guided"
    AUTO = "auto"


class JobStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AlgorithmPolicy(BaseModel):
    """Algorithm selection policy"""
    use_trial_division: bool = True
    trial_division_limit: Optional[int] = 10**7
    use_pollard_rho: bool = True
    pollard_rho_iterations: int = 1000000
    use_ecm: bool = True
    use_equation_bounds: bool = True


class ECMParams(BaseModel):
    """ECM algorithm parameters"""
    stages: List[tuple[int, int]] = Field(
        default=[(10000, 25), (50000, 100), (250000, 200)]
    )


class JobCreate(BaseModel):
    """Request to create a new factorization job"""
    n: str = Field(..., description="The semiprime number to factor")
    mode: JobModeEnum = JobModeEnum.AUTO
    lower_bound: Optional[str] = None
    upper_bound: Optional[str] = None
    csv_token: Optional[str] = None
    equation_config: Optional[Dict[str, Any]] = None
    algorithm_policy: Optional[AlgorithmPolicy] = Field(default_factory=AlgorithmPolicy)
    ecm_params: Optional[ECMParams] = Field(default_factory=ECMParams)
    use_equation: bool = True


class JobResponse(BaseModel):
    """Job details response"""
    id: str
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    n: str
    mode: JobModeEnum
    lower_bound: Optional[str]
    upper_bound: Optional[str]
    status: JobStatusEnum
    progress_percent: int
    current_candidate: Optional[str]
    error_message: Optional[str]
    factors_found: Optional[List[str]]
    total_time_seconds: Optional[int]

    class Config:
        from_attributes = True


class JobControlAction(BaseModel):
    """Job control action"""
    action: str = Field(..., pattern="^(pause|resume|cancel)$")


class JobLogEntry(BaseModel):
    """Single log entry"""
    timestamp: datetime
    level: str
    message: str
    stage: Optional[str]
    payload: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class JobResultEntry(BaseModel):
    """Single result entry"""
    factor: str
    is_prime: Optional[bool]
    certificate: Optional[str]
    found_at: datetime
    found_by_algorithm: str
    elapsed_ms: int

    class Config:
        from_attributes = True


class CSVUploadResponse(BaseModel):
    """CSV upload response"""
    token: str
    filename: str
    rows: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    database: str
    redis: str
    worker: str
