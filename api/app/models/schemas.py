"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field, field_validator
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
    use_ecm_enhanced: bool = True  # Use enhanced ECM with checkpointing
    use_batch_gcd: bool = False  # For bulk operations
    use_bpsw: bool = True  # Use BPSW instead of Miller-Rabin alone
    use_equation_bounds: bool = True
    generate_certificates: bool = False  # Generate primality certificates
    max_time_per_stage: Optional[int] = None  # Max seconds per algorithm stage


class ECMParams(BaseModel):
    """ECM algorithm parameters"""
    stages: List[tuple[int, int]] = Field(
        default=[(10000, 25), (50000, 100), (250000, 200)]
    )
    # Enhanced ECM parameters
    use_checkpointing: bool = True
    checkpoint_interval: int = 100  # Save state every N curves
    B1: Optional[int] = None  # Override B1 (auto-computed if None)
    B2: Optional[int] = None  # Override B2 (auto-computed if None)
    max_curves: Optional[int] = None  # Override max curves
    timeout_seconds: Optional[float] = None  # Timeout for ECM stage


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
    completed_at: Optional[datetime]
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
    elapsed_seconds: Optional[int]
    use_equation: bool
    algorithm_policy: Optional[AlgorithmPolicy]
    ecm_params: Optional[ECMParams]

    @field_validator('algorithm_policy', mode='before')
    @classmethod
    def parse_algorithm_policy(cls, v):
        """Parse algorithm_policy from JSON dict if needed"""
        if v is None:
            return AlgorithmPolicy()
        if isinstance(v, dict):
            return AlgorithmPolicy(**v)
        return v

    @field_validator('ecm_params', mode='before')
    @classmethod
    def parse_ecm_params(cls, v):
        """Parse ecm_params from JSON dict if needed"""
        if v is None:
            return ECMParams()
        if isinstance(v, dict):
            return ECMParams(**v)
        return v

    class Config:
        from_attributes = True


class JobControlAction(BaseModel):
    """Job control action"""
    action: str = Field(..., pattern="^(pause|resume|cancel)$")


class JobLogEntry(BaseModel):
    """Single log entry"""
    id: int
    job_id: str
    timestamp: datetime
    created_at: datetime
    level: str
    message: str
    stage: Optional[str]
    payload: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class JobResultEntry(BaseModel):
    """Single result entry"""
    id: int
    job_id: str
    factor: str
    is_prime: Optional[bool]
    certificate: Optional[str]
    found_at: datetime
    created_at: datetime
    found_by_algorithm: str
    algorithm: str
    elapsed_ms: int
    elapsed_seconds: float

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
