"""
Database models using SQLAlchemy
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey, BigInteger, Enum, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

Base = declarative_base()


class JobStatus(str, enum.Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobMode(str, enum.Enum):
    """Job execution mode"""
    RANGE_SCAN = "range_scan"
    CSV_INPUT = "csv_input"
    EQUATION_GUIDED = "equation_guided"
    AUTO = "auto"  # Automatic algorithm selection


class Job(Base):
    """Main job table"""
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True)  # UUID
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    # Input
    n = Column(Text, nullable=False)  # The semiprime to factor (stored as string for huge numbers)
    mode = Column(Enum(JobMode), nullable=False, default=JobMode.AUTO)
    lower_bound = Column(Text, nullable=True)
    upper_bound = Column(Text, nullable=True)

    # Configuration
    equation_config = Column(JSON, nullable=True)  # Custom equation parameters
    algorithm_policy = Column(JSON, nullable=True)  # Which algorithms to use
    ecm_params = Column(JSON, nullable=True)  # ECM parameters
    use_equation = Column(Boolean, default=True)  # Enable equation-based bounds

    # Status
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    progress_percent = Column(Integer, default=0)
    current_candidate = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # Results
    factors_found = Column(JSON, nullable=True)  # List of factors
    total_time_seconds = Column(Integer, nullable=True)

    # Relationships
    logs = relationship("JobLog", back_populates="job", cascade="all, delete-orphan")
    results = relationship("JobResult", back_populates="job", cascade="all, delete-orphan")

    @property
    def completed_at(self):
        """Alias for finished_at for backwards compatibility"""
        return self.finished_at

    @property
    def elapsed_seconds(self):
        """Calculate elapsed time in seconds"""
        if self.started_at:
            end_time = self.finished_at or datetime.utcnow()
            delta = end_time - self.started_at
            return int(delta.total_seconds())
        return None


class JobLog(Base):
    """Job execution logs"""
    __tablename__ = "job_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String(20))  # INFO, WARNING, ERROR, DEBUG
    message = Column(Text)
    stage = Column(String(50), nullable=True)  # Which algorithm stage
    payload = Column(JSON, nullable=True)  # Additional structured data

    job = relationship("Job", back_populates="logs")

    @property
    def created_at(self):
        """Alias for timestamp for backwards compatibility"""
        return self.timestamp


class JobResult(Base):
    """Factorization results"""
    __tablename__ = "job_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"))
    factor = Column(Text, nullable=False)
    is_prime = Column(Boolean, nullable=True)
    certificate = Column(Text, nullable=True)  # Primality certificate if available
    found_at = Column(DateTime, default=datetime.utcnow)
    found_by_algorithm = Column(String(50))  # Which algorithm found it
    elapsed_ms = Column(Integer)  # Time to find this factor

    job = relationship("Job", back_populates="results")

    @property
    def created_at(self):
        """Alias for found_at for backwards compatibility"""
        return self.found_at

    @property
    def algorithm(self):
        """Alias for found_by_algorithm for backwards compatibility"""
        return self.found_by_algorithm

    @property
    def elapsed_seconds(self):
        """Convert elapsed_ms to seconds"""
        return self.elapsed_ms / 1000.0 if self.elapsed_ms else 0


class Upload(Base):
    """CSV uploads"""
    __tablename__ = "uploads"

    token = Column(String(36), primary_key=True)
    filename = Column(String(255))
    path = Column(String(512))
    rows = Column(Integer)
    status = Column(String(20), default="uploaded")
    created_at = Column(DateTime, default=datetime.utcnow)


class EquationSnapshot(Base):
    """Equation visualization snapshots"""
    __tablename__ = "equation_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"))
    x_min = Column(Text)
    x_max = Column(Text)
    step = Column(Integer)
    points_blob = Column(JSON)  # Array of {x, y, constraint, is_candidate, is_factor}
    created_at = Column(DateTime, default=datetime.utcnow)


class JobRun(Base):
    """Individual algorithm runs for parallel racing"""
    __tablename__ = "job_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"))
    algorithm = Column(String(50), nullable=False)  # rho, ecm, fermat, equation
    status = Column(String(20), default="pending")  # pending, running, completed, cancelled, failed
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    metrics_json = Column(JSON, nullable=True)  # {iterations, curves_done, candidates_tested, etc}
    result = Column(Text, nullable=True)  # Factor if found


class FactorCache(Base):
    """Cache of previously discovered factors"""
    __tablename__ = "factor_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    n_hash = Column(String(64), nullable=False, index=True)  # SHA256 of N
    n = Column(Text, nullable=False)
    factor = Column(Text, nullable=False)
    cofactor = Column(Text, nullable=False)
    method = Column(String(50), nullable=False)  # Algorithm that found it
    is_prime = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# Global session factory (will be initialized by main.py)
SessionFactory = None


# Database connection helper
def get_engine(database_url: str):
    """Create database engine"""
    return create_engine(database_url, pool_pre_ping=True)


def get_session_factory(engine):
    """Create session factory"""
    global SessionFactory
    SessionFactory = sessionmaker(bind=engine)
    return SessionFactory


def init_db(engine):
    """Initialize database tables"""
    Base.metadata.create_all(engine)


def get_db():
    """Dependency for database sessions"""
    db = SessionFactory()
    try:
        yield db
    finally:
        db.close()
