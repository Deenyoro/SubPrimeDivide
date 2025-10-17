"""
Celery worker for factorization tasks
"""
from celery import Celery
import os
from datetime import datetime
import time

# Celery configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery_app = Celery(
    "factor_worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)


@celery_app.task(name="run_factorization")
def run_factorization_task(job_id: str):
    """
    Main factorization task - runs all algorithms in sequence.

    Args:
        job_id: Job UUID

    This task orchestrates the entire factorization pipeline:
    1. Load job configuration
    2. Initialize equation solver if enabled
    3. Try quick algorithms first (trial division, Pollard-rho)
    4. Escalate to ECM if needed
    5. Report results
    """
    from app.models import get_engine, get_session_factory, Job, JobLog, JobResult, JobStatus
    from app.algos import is_prime_mr, pollard_rho, ecm_factor, trial_division_with_wheel
    from app.equations import SemiPrimeEquationSolver
    from primesieve import Iterator
    import gmpy2

    # Get database session
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://factor:factor_dev_password@db:5432/factordb")
    engine = get_engine(DATABASE_URL)
    SessionFactory = get_session_factory(engine)
    db = SessionFactory()

    try:
        # Load job
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"error": "Job not found"}

        # Check if cancelled
        if job.status == JobStatus.CANCELLED:
            return {"status": "cancelled"}

        # Update status
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        db.commit()

        # Parse input
        n = int(job.n)
        add_log(db, job_id, "INFO", f"Starting factorization of {len(str(n))}-digit number", "initialization")

        start_time = time.time()

        # Check if already prime
        add_log(db, job_id, "INFO", "Checking if number is prime...", "primality_check")
        if is_prime_mr(n):
            add_log(db, job_id, "INFO", "Number is prime (no factorization possible)", "primality_check")
            job.status = JobStatus.COMPLETED
            job.finished_at = datetime.utcnow()
            job.total_time_seconds = int(time.time() - start_time)
            job.progress_percent = 100
            db.commit()
            return {"status": "prime", "n": str(n)}

        # Initialize Trurl equation solver if enabled
        solver = None
        if job.use_equation:
            add_log(db, job_id, "INFO", "Initializing Trurl equation-based solver", "equation")
            solver = SemiPrimeEquationSolver(n)

            # Generate diagnostic report
            diagnostic = solver.diagnostic_report()
            add_log(db, job_id, "INFO",
                   f"Semiprime analysis: {diagnostic['pnp_digits']} digits, sqrt has {diagnostic['sqrt_pnp_digits']} digits",
                   "equation",
                   payload={"diagnostics": {k: str(v) if not isinstance(v, (int, float, bool)) else v
                                           for k, v in diagnostic.items() if k not in ['pnp', 'sqrt_pnp']}})

            # Compute bounds using Trurl's method
            lower, upper = solver.find_initial_bounds()
            if not job.lower_bound:
                job.lower_bound = str(lower)
            if not job.upper_bound:
                job.upper_bound = str(upper)
            db.commit()

            # Log bounds with scientific notation
            import math
            lower_exp = math.log10(lower) if lower > 0 else 0
            upper_exp = math.log10(upper) if upper > 0 else 0
            add_log(db, job_id, "INFO",
                   f"Trurl bounds: lower = 10^{lower_exp:.1f}, upper = 10^{upper_exp:.1f}",
                   "equation")

            # Verify inverse relationship (Trurl's key insight: x↑ means y↓)
            # Test with a few sample points in the range
            test_points = []
            if lower < upper:
                mid1 = lower + (upper - lower) // 3
                mid2 = lower + 2 * (upper - lower) // 3
                test_points = [lower, mid1, mid2]

                # Verify the inverse relationship
                all_valid = True
                for i in range(len(test_points) - 1):
                    if not solver.verify_inverse_relationship(test_points[i], test_points[i+1]):
                        all_valid = False
                        break

                if all_valid:
                    add_log(db, job_id, "INFO",
                           "Verified: x increases → y decreases (Trurl inverse relationship holds)",
                           "equation")
                else:
                    add_log(db, job_id, "WARNING",
                           "Inverse relationship may not hold across entire range",
                           "equation")

            # Get search strategy parameters
            strategy = solver.get_search_strategy_params(lower, upper)
            add_log(db, job_id, "INFO",
                   f"Search strategy: {strategy['method']} over {strategy['search_space_digits']}-digit range",
                   "equation",
                   payload=strategy)

        # Parse algorithm policy
        policy = job.algorithm_policy or {}
        use_trial_division = policy.get("use_trial_division", True)
        trial_limit = int(policy.get("trial_division_limit", 10**7))
        use_pollard_rho = policy.get("use_pollard_rho", True)
        pollard_iterations = policy.get("pollard_rho_iterations", 1000000)
        use_ecm = policy.get("use_ecm", True)

        found_factors = []

        # Stage 1: Quick trial division for small factors
        if use_trial_division:
            add_log(db, job_id, "INFO", f"Stage 1: Trial division up to {trial_limit:,}", "trial_division")
            job.progress_percent = 5
            db.commit()

            factor = trial_division_with_wheel(n, limit=trial_limit)
            if factor:
                elapsed_ms = int((time.time() - start_time) * 1000)
                add_log(db, job_id, "INFO", f"Found factor via trial division: {factor}", "trial_division")
                record_factor(db, job_id, factor, "trial_division", elapsed_ms)
                found_factors.append(factor)

                cofactor = n // factor
                if cofactor > 1 and cofactor != factor:
                    if is_prime_mr(cofactor):
                        add_log(db, job_id, "INFO", f"Cofactor {cofactor} is prime", "trial_division")
                        record_factor(db, job_id, cofactor, "trial_division", elapsed_ms)
                        found_factors.append(cofactor)

        # Stage 2: Pollard-rho (cheap probabilistic method)
        if not found_factors and use_pollard_rho:
            add_log(db, job_id, "INFO", f"Stage 2: Pollard-rho ({pollard_iterations:,} iterations)", "pollard_rho")
            job.progress_percent = 15
            db.commit()

            factor = pollard_rho(n, max_iterations=pollard_iterations)
            if factor:
                elapsed_ms = int((time.time() - start_time) * 1000)
                add_log(db, job_id, "INFO", f"Found factor via Pollard-rho: {factor}", "pollard_rho")
                record_factor(db, job_id, factor, "pollard_rho", elapsed_ms)
                found_factors.append(factor)

                cofactor = n // factor
                if cofactor > 1 and cofactor != factor:
                    if is_prime_mr(cofactor):
                        add_log(db, job_id, "INFO", f"Cofactor {cofactor} is prime", "pollard_rho")
                        record_factor(db, job_id, cofactor, "pollard_rho", elapsed_ms)
                        found_factors.append(cofactor)

        # Stage 3: ECM (for medium-sized factors)
        if not found_factors and use_ecm:
            add_log(db, job_id, "INFO", "Stage 3: Elliptic Curve Method (ECM)", "ecm")
            job.progress_percent = 30
            db.commit()

            # Parse ECM parameters
            ecm_params = job.ecm_params or {}
            stages = ecm_params.get("stages", [(10000, 25), (50000, 100), (250000, 200)])

            def ecm_callback(stage_num, total_stages, factor_found):
                job.progress_percent = 30 + int((stage_num / total_stages) * 40)
                add_log(db, job_id, "INFO",
                       f"ECM stage {stage_num+1}/{total_stages} (B1={stages[stage_num][0]}, curves={stages[stage_num][1]})",
                       "ecm")
                db.commit()

            from app.algos.ecm_wrapper import ecm_factor_staged
            factor = ecm_factor_staged(n, stages=stages, callback=ecm_callback)

            if factor:
                elapsed_ms = int((time.time() - start_time) * 1000)
                add_log(db, job_id, "INFO", f"Found factor via ECM: {factor}", "ecm")
                record_factor(db, job_id, factor, "ecm", elapsed_ms)
                found_factors.append(factor)

                cofactor = n // factor
                if cofactor > 1 and cofactor != factor:
                    if is_prime_mr(cofactor):
                        add_log(db, job_id, "INFO", f"Cofactor {cofactor} is prime", "ecm")
                        record_factor(db, job_id, cofactor, "ecm", elapsed_ms)
                        found_factors.append(cofactor)

        # Stage 4: Equation-guided prime search (if enabled and bounds set)
        if not found_factors and solver and job.lower_bound and job.upper_bound:
            add_log(db, job_id, "INFO", "Stage 4: Equation-guided prime search", "equation_search")
            job.progress_percent = 70
            db.commit()

            lower = int(job.lower_bound)
            upper = int(job.upper_bound)

            add_log(db, job_id, "INFO", f"Searching primes in range [{lower:.2e}, {upper:.2e}]", "equation_search")

            # Use primesieve to iterate primes efficiently
            it = Iterator()
            it.skipto(lower)

            prime = it.next_prime()
            count = 0
            check_interval = 10000

            while prime <= upper and prime <= int(gmpy2.isqrt(n)):
                # Check for cancellation
                db.refresh(job)
                if job.status == JobStatus.CANCELLED:
                    add_log(db, job_id, "INFO", "Job cancelled by user", "equation_search")
                    return {"status": "cancelled"}

                # Test if prime divides n
                if n % prime == 0:
                    elapsed_ms = int((time.time() - start_time) * 1000)
                    add_log(db, job_id, "INFO", f"Found factor via Trurl equation search: {prime}", "equation_search")

                    # Get complementary factor
                    cofactor = n // prime

                    # Verify all Trurl constraints
                    x_factor = min(prime, cofactor)
                    y_factor = max(prime, cofactor)
                    constraints = solver.verify_all_constraints(x_factor, y_factor)

                    # Log constraint verification
                    all_satisfied = all(v for v in constraints.values() if v is not None)
                    if all_satisfied:
                        add_log(db, job_id, "INFO",
                               "All Trurl constraints verified: pnp=x*y, equation match, x<y, inverse relationship",
                               "equation_search",
                               payload={"constraints": constraints})
                    else:
                        add_log(db, job_id, "WARNING",
                               f"Some constraints not satisfied: {constraints}",
                               "equation_search",
                               payload={"constraints": constraints})

                    # Compute y using Trurl's equation for verification
                    computed_y = solver.compute_y_from_x(x_factor)
                    add_log(db, job_id, "INFO",
                           f"Trurl equation y = (((pnp^2/x) + x^2) / pnp) yields {computed_y} (actual y = {y_factor})",
                           "equation_search")

                    # Record factors
                    record_factor(db, job_id, prime, "equation_search", elapsed_ms)
                    found_factors.append(prime)

                    if cofactor > 1:
                        if is_prime_mr(cofactor):
                            add_log(db, job_id, "INFO", f"Cofactor {cofactor} is prime", "equation_search")
                            record_factor(db, job_id, cofactor, "equation_search", elapsed_ms)
                            found_factors.append(cofactor)
                    break

                count += 1
                if count % check_interval == 0:
                    # Update progress
                    progress = solver.estimate_progress(prime, lower, upper)
                    job.progress_percent = int(70 + (progress * 0.25))
                    job.current_candidate = str(prime)
                    db.commit()

                prime = it.next_prime()

        # Finalize
        if found_factors:
            job.status = JobStatus.COMPLETED
            job.factors_found = [str(f) for f in found_factors]
            add_log(db, job_id, "INFO", f"Factorization complete: found {len(found_factors)} factors", "complete")
        else:
            job.status = JobStatus.COMPLETED
            add_log(db, job_id, "WARNING", "No factors found with current algorithms", "complete")

        job.finished_at = datetime.utcnow()
        job.total_time_seconds = int(time.time() - start_time)
        job.progress_percent = 100
        db.commit()

        return {"status": "completed", "factors": [str(f) for f in found_factors]}

    except Exception as e:
        add_log(db, job_id, "ERROR", f"Job failed: {str(e)}", "error")
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.finished_at = datetime.utcnow()
            db.commit()
        raise

    finally:
        db.close()


def add_log(db, job_id: str, level: str, message: str, stage: str, payload: dict = None):
    """Helper to add log entry"""
    from app.models import JobLog
    log = JobLog(
        job_id=job_id,
        level=level,
        message=message,
        stage=stage,
        payload=payload
    )
    db.add(log)
    db.commit()


def record_factor(db, job_id: str, factor: int, algorithm: str, elapsed_ms: int):
    """Helper to record a found factor"""
    from app.models import JobResult
    from app.algos import is_prime_mr

    result = JobResult(
        job_id=job_id,
        factor=str(factor),
        is_prime=is_prime_mr(factor),
        found_by_algorithm=algorithm,
        elapsed_ms=elapsed_ms
    )
    db.add(result)
    db.commit()
