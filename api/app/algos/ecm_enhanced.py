"""
Enhanced ECM using passagemath-libecm Python bindings with checkpointing.

This provides:
1. Direct Python bindings to GMP-ECM (faster than subprocess)
2. Checkpointing and resume capability
3. Better progress tracking
4. Configurable timeouts and budgets
"""

import gmpy2
import json
import time
from typing import Optional, Callable, Dict, List
from dataclasses import dataclass, asdict


@dataclass
class ECMCheckpoint:
    """Checkpoint for resuming ECM computation"""
    n: str  # Number being factored
    B1: int
    B2: int
    curves_total: int
    curves_completed: int
    sigma_values: List[int]  # Sigmas of curves already tried
    time_elapsed: float
    created_at: float

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @staticmethod
    def from_json(json_str: str) -> 'ECMCheckpoint':
        data = json.loads(json_str)
        return ECMCheckpoint(**data)

    def save(self, filepath: str):
        with open(filepath, 'w') as f:
            f.write(self.to_json())

    @staticmethod
    def load(filepath: str) -> 'ECMCheckpoint':
        with open(filepath, 'r') as f:
            return ECMCheckpoint.from_json(f.read())


try:
    # Try to import passagemath-libecm
    from sage.all import ecm
    HAS_SAGE_ECM = True
except ImportError:
    HAS_SAGE_ECM = False


def ecm_factor_enhanced(
    n: int,
    B1: int = 1_000_000,
    B2: Optional[int] = None,
    curves: int = 1000,
    timeout: Optional[float] = None,
    checkpoint_interval: int = 100,
    checkpoint_callback: Optional[Callable[[ECMCheckpoint], None]] = None,
    resume_from: Optional[ECMCheckpoint] = None
) -> Optional[int]:
    """
    Enhanced ECM factorization with checkpointing and timeout support.

    Args:
        n: Number to factor
        B1: Stage 1 bound
        B2: Stage 2 bound (if None, auto-computed from B1)
        curves: Number of curves to try
        timeout: Maximum time in seconds (None = no limit)
        checkpoint_interval: Save checkpoint every N curves
        checkpoint_callback: Function to call with checkpoint data
        resume_from: Checkpoint to resume from

    Returns:
        A non-trivial factor if found, None otherwise
    """
    if n <= 1:
        return None

    # Auto-compute B2 if not provided (typical: B2 = 100 * B1)
    if B2 is None:
        B2 = 100 * B1

    # Initialize from checkpoint or start fresh
    if resume_from:
        if int(resume_from.n) != n:
            raise ValueError("Checkpoint is for a different number")
        start_curve = resume_from.curves_completed
        sigma_used = set(resume_from.sigma_values)
        time_offset = resume_from.time_elapsed
    else:
        start_curve = 0
        sigma_used = set()
        time_offset = 0.0

    start_time = time.time()

    # Try using passagemath-libecm if available
    if HAS_SAGE_ECM:
        for curve_idx in range(start_curve, curves):
            # Check timeout
            if timeout and (time.time() - start_time + time_offset) > timeout:
                break

            # Generate sigma (seed for curve)
            sigma = _generate_sigma(sigma_used)
            sigma_used.add(sigma)

            try:
                # Use Sage's ECM interface
                result = ecm.ecm(n, B1, B2=B2, sigma=sigma)

                # ecm.ecm returns a factor or raises an exception if none found
                if isinstance(result, (int, gmpy2.mpz)):
                    factor = int(result)
                    if 1 < factor < n:
                        return factor
            except Exception:
                # No factor found with this curve
                pass

            # Checkpoint
            if checkpoint_callback and (curve_idx + 1) % checkpoint_interval == 0:
                checkpoint = ECMCheckpoint(
                    n=str(n),
                    B1=B1,
                    B2=B2,
                    curves_total=curves,
                    curves_completed=curve_idx + 1,
                    sigma_values=list(sigma_used),
                    time_elapsed=time.time() - start_time + time_offset,
                    created_at=time.time()
                )
                checkpoint_callback(checkpoint)

    else:
        # Fallback: use gmpy2 with our own ECM implementation
        # (Less efficient but works without Sage)
        return _ecm_gmpy2_fallback(
            n, B1, B2, curves, start_curve, sigma_used,
            timeout, time_offset, start_time,
            checkpoint_interval, checkpoint_callback
        )

    return None


def _generate_sigma(used_sigmas: set) -> int:
    """Generate a random sigma value that hasn't been used"""
    state = gmpy2.random_state(int(time.time() * 1000000) % (2**32))
    while True:
        sigma = int(gmpy2.mpz_urandomb(state, 32))
        if sigma >= 6 and sigma not in used_sigmas:
            return sigma


def _ecm_gmpy2_fallback(
    n: int,
    B1: int,
    B2: int,
    curves: int,
    start_curve: int,
    sigma_used: set,
    timeout: Optional[float],
    time_offset: float,
    start_time: float,
    checkpoint_interval: int,
    checkpoint_callback: Optional[Callable]
) -> Optional[int]:
    """
    Fallback ECM implementation using gmpy2 (when Sage not available).

    This is a simplified ECM that's less efficient than GMP-ECM but
    works with only gmpy2.
    """
    # Simplified ECM using Suyama's parameterization
    # This is less efficient than full GMP-ECM but works

    n_mpz = gmpy2.mpz(n)

    for curve_idx in range(start_curve, curves):
        # Check timeout
        if timeout and (time.time() - start_time + time_offset) > timeout:
            break

        # Generate curve parameters
        sigma = _generate_sigma(sigma_used)
        sigma_used.add(sigma)

        # Simplified ECM stage 1
        factor = _ecm_stage1_simple(n_mpz, B1, sigma)

        if factor and 1 < factor < n:
            return int(factor)

        # Checkpoint
        if checkpoint_callback and (curve_idx + 1) % checkpoint_interval == 0:
            checkpoint = ECMCheckpoint(
                n=str(n),
                B1=B1,
                B2=B2,
                curves_total=curves,
                curves_completed=curve_idx + 1,
                sigma_values=list(sigma_used),
                time_elapsed=time.time() - start_time + time_offset,
                created_at=time.time()
            )
            checkpoint_callback(checkpoint)

    return None


def _ecm_stage1_simple(n: gmpy2.mpz, B1: int, sigma: int) -> Optional[int]:
    """
    Simplified ECM stage 1 using Suyama's parameterization.

    This is a basic implementation for when full GMP-ECM isn't available.
    """
    # Suyama's parameterization: convert sigma to (a, x, z)
    u = gmpy2.mpz(sigma * sigma - 5)
    v = gmpy2.mpz(4 * sigma)

    # Compute curve parameter a
    a = gmpy2.f_mod((v - u)**3 * (3*u + v), n)
    a = gmpy2.f_mod(a * gmpy2.invert(16*u*v*v*v, n), n) - 2

    # Starting point
    x = gmpy2.f_mod(u*u*u, n)
    z = gmpy2.f_mod(v*v*v, n)

    # Stage 1: multiply point by primes up to B1
    prime = gmpy2.mpz(2)
    while prime <= B1:
        # Multiply point by prime^k where prime^k <= B1
        q = prime
        while q * prime <= B1:
            q *= prime

        # Scalar multiplication by q
        for _ in range(int(q)):
            x, z = _ecm_add(x, z, x, z, a, n)

        prime = gmpy2.next_prime(prime)

    # Check for factor
    g = gmpy2.gcd(z, n)
    if 1 < g < n:
        return int(g)

    return None


def _ecm_add(x1: gmpy2.mpz, z1: gmpy2.mpz,
             x2: gmpy2.mpz, z2: gmpy2.mpz,
             a: gmpy2.mpz, n: gmpy2.mpz) -> tuple:
    """
    Elliptic curve point addition in projective coordinates.

    This is a simplified version for ECM.
    """
    # Point doubling when (x1,z1) == (x2,z2)
    if x1 == x2 and z1 == z2:
        # Double: 2*(x1:z1)
        u = gmpy2.f_mod((x1 + z1)**2, n)
        v = gmpy2.f_mod((x1 - z1)**2, n)
        x3 = gmpy2.f_mod(u * v, n)
        z3 = gmpy2.f_mod((u - v) * (v + gmpy2.f_mod((a+2)//4 * (u - v), n)), n)
        return (x3, z3)

    # General addition
    u = gmpy2.f_mod((x1 - z1) * (x2 + z2), n)
    v = gmpy2.f_mod((x1 + z1) * (x2 - z2), n)
    x3 = gmpy2.f_mod(z1 * (u + v)**2, n)
    z3 = gmpy2.f_mod(x1 * (u - v)**2, n)

    return (x3, z3)


def suggest_ecm_params_enhanced(digit_count: int, time_budget: Optional[float] = None) -> Dict:
    """
    Suggest ECM parameters based on number size and optional time budget.

    Args:
        digit_count: Number of digits in the composite
        time_budget: Optional time budget in seconds

    Returns:
        Dictionary with B1, B2, curves, and estimated time
    """
    expected_factor_digits = digit_count // 2

    # Base recommendations (no time constraint)
    if expected_factor_digits <= 25:
        params = {'B1': 11_000, 'curves': 100, 'est_time_mins': 1}
    elif expected_factor_digits <= 30:
        params = {'B1': 50_000, 'curves': 200, 'est_time_mins': 10}
    elif expected_factor_digits <= 35:
        params = {'B1': 250_000, 'curves': 500, 'est_time_mins': 60}
    elif expected_factor_digits <= 40:
        params = {'B1': 1_000_000, 'curves': 1000, 'est_time_mins': 180}
    elif expected_factor_digits <= 45:
        params = {'B1': 3_000_000, 'curves': 2000, 'est_time_mins': 720}
    elif expected_factor_digits <= 50:
        params = {'B1': 11_000_000, 'curves': 4000, 'est_time_mins': 2880}
    else:
        params = {'B1': 43_000_000, 'curves': 8000, 'est_time_mins': 10080}

    # Adjust for time budget if provided
    if time_budget:
        budget_mins = time_budget / 60
        if budget_mins < params['est_time_mins']:
            # Scale down curves to fit budget
            scale = budget_mins / params['est_time_mins']
            params['curves'] = max(10, int(params['curves'] * scale))
            params['est_time_mins'] = budget_mins

    params['B2'] = params['B1'] * 100
    params['digit_range'] = f"{expected_factor_digits-5}-{expected_factor_digits+5} digits"

    return params
