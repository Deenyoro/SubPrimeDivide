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
    1. Primality check (exit if n is prime)
    2. Trial division (fast check for small factors)
    3. Pollard-rho (probabilistic for medium factors)
    4. Shor's algorithm - classical emulation (order-finding on smooth orders)
    5. ECM (elliptic curve method)
    6. Advanced ECM (for 30+ digit factors)
    7. Trurl equation-guided search (if enabled)
    8. Report results
    """
    from app.models import get_engine, get_session_factory, Job, JobLog, JobResult, JobStatus
    from app.algos import (
        is_prime_mr, is_prime_bpsw, is_prime_fast,
        pollard_rho, ecm_factor, trial_division_with_wheel, shor_classical_multi_attempt,
        ecm_factor_enhanced, suggest_ecm_params_enhanced,
        generate_certificate_simple
    )
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

        # Parse algorithm policy to determine primality test
        policy = job.algorithm_policy or {}
        use_bpsw = policy.get("use_bpsw", True)
        generate_certs = policy.get("generate_certificates", False)

        # Check if already prime using BPSW (more rigorous) or Miller-Rabin
        add_log(db, job_id, "INFO",
               f"Checking if number is prime using {'BPSW' if use_bpsw else 'Miller-Rabin'}...",
               "primality_check")

        primality_test = is_prime_fast if use_bpsw else is_prime_mr
        if primality_test(n):
            add_log(db, job_id, "INFO", "Number is prime (no factorization possible)", "primality_check")

            # Generate certificate if requested
            if generate_certs:
                try:
                    cert = generate_certificate_simple(n)
                    if cert:
                        add_log(db, job_id, "INFO",
                               f"Generated primality certificate with {len(cert.steps)} steps",
                               "primality_check",
                               payload={"certificate": cert.to_json()})
                except Exception as e:
                    add_log(db, job_id, "WARNING",
                           f"Failed to generate certificate: {e}",
                           "primality_check")

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

        # Algorithm policy already parsed above for primality test
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
                record_factor(db, job_id, factor, "trial_division", elapsed_ms,
                            primality_test, generate_certs)
                found_factors.append(factor)

                cofactor = n // factor
                if cofactor > 1 and cofactor != factor:
                    if primality_test(cofactor):
                        add_log(db, job_id, "INFO", f"Cofactor {cofactor} is prime", "trial_division")
                        record_factor(db, job_id, cofactor, "trial_division", elapsed_ms,
                                    primality_test, generate_certs)
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
                record_factor(db, job_id, factor, "pollard_rho", elapsed_ms,
                            primality_test, generate_certs)
                found_factors.append(factor)

                cofactor = n // factor
                if cofactor > 1 and cofactor != factor:
                    if primality_test(cofactor):
                        add_log(db, job_id, "INFO", f"Cofactor {cofactor} is prime", "pollard_rho")
                        record_factor(db, job_id, cofactor, "pollard_rho", elapsed_ms,
                                    primality_test, generate_certs)
                        found_factors.append(cofactor)

        # Stage 3: Shor's Algorithm (Classical Emulation)
        if not found_factors and policy.get("use_shor_classical", True):
            add_log(db, job_id, "INFO", "Stage 3: Shor's algorithm (classical emulation)", "shor_classical")
            job.progress_percent = 25
            db.commit()

            # Educational note about this stage
            add_log(db, job_id, "INFO",
                   "Note: This uses classical order-finding (not quantum). "
                   "Works efficiently when orders are smooth, similar to Pollard's p-1.",
                   "shor_classical")

            # Try with increasing smoothness bounds
            B_values = [10000, 50000, 200000, 1000000]

            for i, B in enumerate(B_values):
                # Check for cancellation
                db.refresh(job)
                if job.status == JobStatus.CANCELLED:
                    add_log(db, job_id, "INFO", "Job cancelled by user", "shor_classical")
                    return {"status": "cancelled"}

                add_log(db, job_id, "INFO",
                       f"Shor classical: trying smoothness bound B={B:,}",
                       "shor_classical")

                factor, all_diagnostics = shor_classical_multi_attempt(
                    n,
                    B_values=[B],
                    max_attempts_per_B=3  # Try 3 random bases per B value
                )

                if factor:
                    elapsed_ms = int((time.time() - start_time) * 1000)

                    # Log the successful attempt's details
                    successful_diag = [d for d in all_diagnostics if 'method' in d and 'failed' not in d.get('method', '')]
                    if successful_diag:
                        diag = successful_diag[-1]
                        add_log(db, job_id, "INFO",
                               f"Shor classical success: method={diag.get('method')}, a={diag.get('a')}, "
                               f"order={diag.get('order_found', 'N/A')}, B={B:,}",
                               "shor_classical",
                               payload=diag)

                        # Add educational explanation
                        if diag.get('order_found'):
                            r = diag['order_found']
                            explanation = (
                                f"Found order r={r} of a={diag.get('a')} mod n. "
                                f"Order is {'even' if r % 2 == 0 else 'odd'}. "
                            )
                            if diag.get('shor_condition_satisfied'):
                                explanation += f"Shor's conditions satisfied: r even and a^(r/2) ≢ ±1 (mod n). "
                                explanation += f"Used gcd(a^(r/2) ± 1, n) to extract factor."
                            add_log(db, job_id, "INFO", explanation, "shor_classical")

                    add_log(db, job_id, "INFO", f"Found factor via Shor classical: {factor}", "shor_classical")
                    record_factor(db, job_id, factor, "shor_classical", elapsed_ms,
                                primality_test, generate_certs)
                    found_factors.append(factor)

                    cofactor = n // factor
                    if cofactor > 1 and cofactor != factor:
                        if primality_test(cofactor):
                            add_log(db, job_id, "INFO", f"Cofactor {cofactor} is prime", "shor_classical")
                            record_factor(db, job_id, cofactor, "shor_classical", elapsed_ms,
                                        primality_test, generate_certs)
                            found_factors.append(cofactor)
                    break

                # Update progress
                job.progress_percent = 25 + int((i + 1) / len(B_values) * 5)
                db.commit()

            if not found_factors:
                add_log(db, job_id, "INFO",
                       "Shor classical: no factor found (order likely not smooth within B bounds)",
                       "shor_classical")

        # Stage 4: ECM (for medium-sized factors)
        if not found_factors and use_ecm:
            add_log(db, job_id, "INFO", "Stage 4: Elliptic Curve Method (ECM)", "ecm")
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
                record_factor(db, job_id, factor, "ecm", elapsed_ms,
                            primality_test, generate_certs)
                found_factors.append(factor)

                cofactor = n // factor
                if cofactor > 1 and cofactor != factor:
                    if primality_test(cofactor):
                        add_log(db, job_id, "INFO", f"Cofactor {cofactor} is prime", "ecm")
                        record_factor(db, job_id, cofactor, "ecm", elapsed_ms,
                                    primality_test, generate_certs)
                        found_factors.append(cofactor)

        # Stage 5: Advanced ECM (for 30+ digit factors)
        if not found_factors and use_ecm:
            digit_count = len(str(n))
            if digit_count >= 30:  # ECM is most effective for larger numbers
                add_log(db, job_id, "INFO", "Stage 5: Advanced ECM (GMP-ECM)", "ecm_advanced")
                job.progress_percent = 60
                db.commit()

                try:
                    from app.algos.ecm_advanced import ecm_factor_staged_advanced, suggest_ecm_params

                    # Get recommended parameters
                    params = suggest_ecm_params(digit_count)
                    add_log(db, job_id, "INFO",
                           f"ECM parameters: B1={params['B1']}, curves={params['curves']}, "
                           f"expected time: {params['expected_time']}",
                           "ecm_advanced",
                           payload=params)

                    def ecm_advanced_callback(stage_num, total_stages, B1, curves):
                        progress = 60 + int((stage_num / total_stages) * 15)
                        job.progress_percent = progress
                        add_log(db, job_id, "INFO",
                               f"ECM advanced stage {stage_num+1}/{total_stages} (B1={B1:,}, curves={curves:,})",
                               "ecm_advanced")
                        db.commit()

                    factor = ecm_factor_staged_advanced(n, digit_count, callback=ecm_advanced_callback)

                    if factor:
                        elapsed_ms = int((time.time() - start_time) * 1000)
                        add_log(db, job_id, "INFO", f"Found factor via Advanced ECM: {factor}", "ecm_advanced")
                        record_factor(db, job_id, factor, "ecm_advanced", elapsed_ms,
                                    primality_test, generate_certs)
                        found_factors.append(factor)

                        cofactor = n // factor
                        if cofactor > 1 and cofactor != factor:
                            if primality_test(cofactor):
                                add_log(db, job_id, "INFO", f"Cofactor {cofactor} is prime", "ecm_advanced")
                                record_factor(db, job_id, cofactor, "ecm_advanced", elapsed_ms,
                                            primality_test, generate_certs)
                                found_factors.append(cofactor)
                except ImportError:
                    add_log(db, job_id, "WARNING",
                           "Advanced ECM (passagemath-libecm) not available. Skipping.",
                           "ecm_advanced")

        # Stage 6: CADO-NFS (for 200+ digit semiprimes - production GNFS)
        if not found_factors:
            digit_count = len(str(n))
            if digit_count >= 200:  # CADO-NFS is the right tool for RSA-scale numbers
                add_log(db, job_id, "INFO", "Stage 6: CADO-NFS (General Number Field Sieve)", "cado_nfs")
                job.progress_percent = 75
                db.commit()

                try:
                    from app.algos.cado_nfs import cado_nfs_factor, estimate_cado_runtime, HAS_CADO

                    if HAS_CADO:
                        # Get runtime estimate
                        estimate = estimate_cado_runtime(digit_count)
                        add_log(db, job_id, "INFO",
                               f"CADO-NFS est: {estimate['estimated_time']}, "
                               f"recommended CPU cores: {estimate['cpu_cores']}, "
                               f"memory: {estimate['memory_gb']} GB",
                               "cado_nfs",
                               payload=estimate)

                        # Get expected factor size from Trurl bounds (if available)
                        expected_factor_digits = None
                        if solver and job.lower_bound:
                            import math
                            try:
                                lower = int(float(job.lower_bound))
                                expected_factor_digits = int(math.log10(lower))
                                add_log(db, job_id, "INFO",
                                       f"Using Trurl hint for polynomial selection: expected factor ~10^{expected_factor_digits}",
                                       "cado_nfs")
                            except:
                                pass

                        # Setup CADO callback for progress updates
                        def cado_callback(log_line):
                            # Stream CADO-NFS logs to database
                            add_log(db, job_id, "INFO", log_line, "cado_nfs")

                            # Check for cancellation periodically
                            db.refresh(job)
                            if job.status == JobStatus.CANCELLED:
                                raise Exception("Job cancelled by user")

                        # Run CADO-NFS (this may take weeks/months for RSA-260)
                        add_log(db, job_id, "INFO",
                               "CADO-NFS starting... This may run for weeks/months. "
                               "You can safely cancel and resume later (CADO checkpoints automatically).",
                               "cado_nfs")

                        result = cado_nfs_factor(
                            n,
                            threads=4,  # TODO: Make configurable
                            expected_factor_digits=expected_factor_digits,
                            callback=cado_callback,
                            timeout=None  # No timeout - let it run
                        )

                        if result:
                            p, q = result
                            elapsed_ms = int((time.time() - start_time) * 1000)
                            add_log(db, job_id, "INFO", f"CADO-NFS found factors: {p} × {q}", "cado_nfs")

                            # Record both factors
                            record_factor(db, job_id, p, "cado_nfs", elapsed_ms)
                            record_factor(db, job_id, q, "cado_nfs", elapsed_ms)
                            found_factors.extend([p, q])
                    else:
                        add_log(db, job_id, "WARNING",
                               "CADO-NFS not available. For 200+ digit semiprimes, "
                               "CADO-NFS (General Number Field Sieve) is the recommended method. "
                               "Falling back to slower alternatives...",
                               "cado_nfs")

                except Exception as e:
                    if "cancelled" in str(e).lower():
                        add_log(db, job_id, "INFO", "CADO-NFS cancelled by user", "cado_nfs")
                        return {"status": "cancelled"}
                    else:
                        add_log(db, job_id, "WARNING",
                               f"CADO-NFS error: {e}. Continuing with other methods...",
                               "cado_nfs")

        # Stage 7: Equation-guided prime search (if enabled and bounds set)
        if not found_factors and solver and job.lower_bound and job.upper_bound:
            add_log(db, job_id, "INFO", "Stage 6: Equation-guided prime search (Trurl method)", "equation_search")
            job.progress_percent = 75
            db.commit()

            # Convert from scientific notation if needed (e.g., "1e90" -> 10^90)
            lower = int(float(job.lower_bound))
            upper = int(float(job.upper_bound))

            # Determine which prime iterator to use
            MAX_PRIMESIEVE = 2**64 - 1
            use_arbitrary_precision = lower > MAX_PRIMESIEVE or upper > MAX_PRIMESIEVE

            if use_arbitrary_precision:
                add_log(db, job_id, "INFO",
                       f"Search range [{lower:.2e}, {upper:.2e}] exceeds primesieve limits. "
                       f"Switching to arbitrary-precision prime iteration (gmpy2).",
                       "equation_search")
                add_log(db, job_id, "WARNING",
                       f"Note: Arbitrary-precision iteration is ~1000x slower than primesieve. "
                       f"For RSA-class numbers (200+ digits), this will take extremely long. "
                       f"Consider using CADO-NFS for numbers this large.",
                       "equation_search")

                # Use gmpy2.next_prime for arbitrary precision
                prime = gmpy2.next_prime(gmpy2.mpz(lower))
                count = 0
                check_interval = 1000  # Check less frequently for large numbers

                while prime <= upper and prime <= gmpy2.isqrt(gmpy2.mpz(n)):
                    # Check for cancellation
                    db.refresh(job)
                    if job.status == JobStatus.CANCELLED:
                        add_log(db, job_id, "INFO", "Job cancelled by user", "equation_search")
                        return {"status": "cancelled"}

                    # Test if prime divides n
                    if n % int(prime) == 0:
                        elapsed_ms = int((time.time() - start_time) * 1000)
                        add_log(db, job_id, "INFO", f"Found factor via Trurl equation search: {prime}", "equation_search")

                        prime_int = int(prime)
                        cofactor = n // prime_int

                        # Verify all Trurl constraints
                        x_factor = min(prime_int, cofactor)
                        y_factor = max(prime_int, cofactor)
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
                        record_factor(db, job_id, prime_int, "equation_search", elapsed_ms,
                                    primality_test, generate_certs)
                        found_factors.append(prime_int)

                        if cofactor > 1:
                            if primality_test(cofactor):
                                add_log(db, job_id, "INFO", f"Cofactor {cofactor} is prime", "equation_search")
                                record_factor(db, job_id, cofactor, "equation_search", elapsed_ms,
                                            primality_test, generate_certs)
                                found_factors.append(cofactor)
                        break

                    count += 1
                    if count % check_interval == 0:
                        # Update progress
                        progress = solver.estimate_progress(int(prime), lower, upper)
                        job.progress_percent = int(75 + (progress * 0.20))
                        job.current_candidate = str(prime)
                        add_log(db, job_id, "INFO",
                               f"Checked {count:,} primes. Current: {prime:.6e}",
                               "equation_search")
                        db.commit()

                    prime = gmpy2.next_prime(prime)

            else:
                # Use fast primesieve for numbers < 2^64
                add_log(db, job_id, "INFO", f"Using primesieve for fast iteration in range [{lower:.2e}, {upper:.2e}]", "equation_search")

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
                        record_factor(db, job_id, prime, "equation_search", elapsed_ms,
                                    primality_test, generate_certs)
                        found_factors.append(prime)

                        if cofactor > 1:
                            if primality_test(cofactor):
                                add_log(db, job_id, "INFO", f"Cofactor {cofactor} is prime", "equation_search")
                                record_factor(db, job_id, cofactor, "equation_search", elapsed_ms,
                                            primality_test, generate_certs)
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


def record_factor(db, job_id: str, factor: int, algorithm: str, elapsed_ms: int,
                 primality_test=None, generate_cert=False):
    """
    Helper to record a found factor.

    Args:
        db: Database session
        job_id: Job ID
        factor: The factor found
        algorithm: Algorithm that found the factor
        elapsed_ms: Time taken
        primality_test: Function to test primality (default: is_prime_fast)
        generate_cert: Whether to generate a primality certificate
    """
    from app.models import JobResult
    from app.algos import is_prime_fast, generate_certificate_simple

    if primality_test is None:
        primality_test = is_prime_fast

    is_prime = primality_test(factor)

    # Generate certificate if requested and factor is prime
    certificate = None
    if generate_cert and is_prime:
        try:
            cert = generate_certificate_simple(factor)
            if cert:
                certificate = cert.to_json()
        except Exception as e:
            add_log(db, job_id, "WARNING",
                   f"Failed to generate certificate for factor {factor}: {e}",
                   algorithm)

    result = JobResult(
        job_id=job_id,
        factor=str(factor),
        is_prime=is_prime,
        certificate=certificate,
        found_by_algorithm=algorithm,
        elapsed_ms=elapsed_ms
    )
    db.add(result)
    db.commit()
