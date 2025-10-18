"""
Shor's Algorithm - Classical Emulation

This implements the classical parts of Shor's algorithm, using classical order-finding
techniques. Unlike a quantum computer which can find the order efficiently via the
Quantum Fourier Transform, this uses classical smooth-exponent methods.

Educational note: The quantum advantage in Shor's algorithm comes from QUANTUM period
finding. This implementation uses the same post-processing steps as Shor but with
classical order-finding, which is only efficient when the order is smooth (similar
to Pollard's p-1 algorithm).

Reference: Shor, P.W. (1997). "Polynomial-Time Algorithms for Prime Factorization
and Discrete Logarithms on a Quantum Computer"
"""
import gmpy2
from gmpy2 import mpz, powmod, gcd, is_prime
from typing import Optional, Dict, Any
import random


def generate_primes_up_to(limit: int) -> list[int]:
    """
    Generate all primes up to limit using Sieve of Eratosthenes.

    Args:
        limit: Upper bound for prime generation

    Returns:
        List of primes <= limit
    """
    if limit < 2:
        return []

    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False

    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            for j in range(i*i, limit + 1, i):
                sieve[j] = False

    return [i for i in range(2, limit + 1) if sieve[i]]


def build_smooth_exponent(B: int) -> mpz:
    """
    Build M = ∏_{q ≤ B} q^{⌊log_q B⌋}

    This is the product of all prime powers up to B, which is a multiple
    of all "B-smooth" numbers.

    Args:
        B: Smoothness bound

    Returns:
        The smooth exponent M
    """
    M = mpz(1)
    primes = generate_primes_up_to(B)

    for q in primes:
        qq = mpz(q)
        # Find largest e such that q^e <= B
        e = 1
        while qq ** (e + 1) <= B:
            e += 1
        M *= qq ** e

    return M


def find_order_classical(a: int, n: int, B: int) -> Optional[int]:
    """
    Classical order-finding using smooth exponent squeeze.

    Tries to find the order r of a mod n (smallest r > 0 such that a^r ≡ 1 mod n)
    by building a smooth multiple and reducing it.

    This only works when the order is B-smooth (all prime factors <= B).

    Args:
        a: Base
        n: Modulus
        B: Smoothness bound

    Returns:
        The order r if found, None otherwise
    """
    a = mpz(a)
    n = mpz(n)

    # Build M = product of prime powers up to B
    M = build_smooth_exponent(B)

    # Try to squeeze M down to the actual order r
    # Key insight: if a^M ≡ 1 (mod n), then the order r divides M
    # We remove prime factors from M until it stops working
    if powmod(a, M, n) != 1:
        return None  # Order is not B-smooth

    primes = generate_primes_up_to(B)

    for q in primes:
        while M % q == 0:
            M_reduced = M // q
            if powmod(a, M_reduced, n) == 1:
                M = M_reduced
            else:
                break  # Can't reduce further

    r = int(M)

    # Verify we found the order
    if powmod(a, r, n) == 1:
        return r

    return None


def shor_classical_post_processing(a: int, r: int, n: int) -> Optional[int]:
    """
    Shor's classical post-processing step.

    Given the order r of a mod n, try to extract a factor using:
    - If r is even and a^(r/2) ≢ -1 (mod n), then gcd(a^(r/2) ± 1, n) may be a factor

    This is the same post-processing used in Shor's quantum algorithm.

    Args:
        a: Base
        r: Order of a mod n
        n: Number to factor

    Returns:
        A non-trivial factor if found, None otherwise
    """
    n = mpz(n)

    # Shor's algorithm requires r to be even
    if r % 2 != 0:
        return None

    # Compute a^(r/2) mod n
    ar2 = powmod(a, r // 2, n)

    # Check that a^(r/2) ≢ ±1 (mod n)
    if ar2 == 1 or ar2 == n - 1:
        return None

    # Try gcd(a^(r/2) - 1, n)
    g1 = gcd(ar2 - 1, n)
    if 1 < g1 < n:
        return int(g1)

    # Try gcd(a^(r/2) + 1, n)
    g2 = gcd(ar2 + 1, n)
    if 1 < g2 < n:
        return int(g2)

    return None


def shor_classical_one_shot(
    n: int,
    B: int = 100000,
    a: Optional[int] = None
) -> tuple[Optional[int], Dict[str, Any]]:
    """
    Single attempt at Shor's algorithm using classical order-finding.

    This combines:
    1. Classical order-finding (only works for smooth orders)
    2. Shor's classical post-processing (gcd steps)

    Args:
        n: Number to factor
        B: Smoothness bound for order-finding
        a: Base to use (random if None)

    Returns:
        Tuple of (factor or None, diagnostic info dict)
    """
    n = mpz(n)

    # Choose random a if not provided
    if a is None:
        a = random.randint(2, int(n) - 2)
    a = mpz(a)

    diagnostics = {
        'a': int(a),
        'B': B,
        'gcd_check': None,
        'order_found': None,
        'order_is_even': None,
        'shor_condition_satisfied': None,
    }

    # Quick gcd check - sometimes we get lucky
    g = gcd(a, n)
    diagnostics['gcd_check'] = int(g)
    if g != 1 and g != n:
        diagnostics['method'] = 'gcd_lucky'
        return int(g), diagnostics

    # Try Pollard p-1 style attempt first (faster)
    M = build_smooth_exponent(B)
    am_minus_1 = powmod(a, M, n) - 1
    g = gcd(am_minus_1, n)
    if 1 < g < n:
        diagnostics['method'] = 'pollard_p_minus_1_style'
        diagnostics['smooth_exponent'] = str(M)[:100] + '...' if len(str(M)) > 100 else str(M)
        return int(g), diagnostics

    # Try to find the actual order
    r = find_order_classical(a, n, B)

    if r is None:
        diagnostics['method'] = 'order_finding_failed'
        diagnostics['reason'] = 'order is not B-smooth or exceeds bound'
        return None, diagnostics

    diagnostics['order_found'] = r
    diagnostics['order_is_even'] = (r % 2 == 0)

    # Apply Shor's post-processing
    factor = shor_classical_post_processing(a, r, n)

    if factor:
        diagnostics['method'] = 'shor_post_processing'
        diagnostics['shor_condition_satisfied'] = True
        ar2 = powmod(a, r // 2, n)
        diagnostics['a_to_r_over_2_mod_n'] = str(ar2)[:100] + '...' if len(str(ar2)) > 100 else str(ar2)
        diagnostics['explanation'] = f'Found even order r={r}, a^(r/2) ≢ ±1 (mod n), used gcd(a^(r/2)±1, n)'
    else:
        diagnostics['method'] = 'shor_post_processing_failed'
        diagnostics['shor_condition_satisfied'] = False
        if r % 2 != 0:
            diagnostics['reason'] = 'order is odd (Shor requires even order)'
        else:
            diagnostics['reason'] = 'a^(r/2) ≡ ±1 (mod n) (unlucky case)'

    return factor, diagnostics


def shor_classical_multi_attempt(
    n: int,
    B_values: list[int] = None,
    max_attempts_per_B: int = 5
) -> tuple[Optional[int], list[Dict[str, Any]]]:
    """
    Try Shor classical with multiple smoothness bounds and random bases.

    Args:
        n: Number to factor
        B_values: List of smoothness bounds to try (default: [10000, 50000, 200000, 1000000])
        max_attempts_per_B: Number of random bases to try per B value

    Returns:
        Tuple of (factor or None, list of all attempt diagnostics)
    """
    if B_values is None:
        B_values = [10000, 50000, 200000, 1000000]

    all_diagnostics = []

    for B in B_values:
        for attempt in range(max_attempts_per_B):
            # Use different random bases
            factor, diag = shor_classical_one_shot(n, B=B)
            diag['B'] = B
            diag['attempt'] = attempt + 1
            all_diagnostics.append(diag)

            if factor:
                return factor, all_diagnostics

    return None, all_diagnostics


# Simulated QFT mode (educational only - uses hidden order)
def shor_simulated_qft(
    n: int,
    a: Optional[int] = None,
    true_order: Optional[int] = None
) -> tuple[Optional[int], Dict[str, Any]]:
    """
    EDUCATIONAL SIMULATION ONLY - simulates Shor's algorithm with a quantum computer.

    This simulates what would happen if we had access to a quantum period-finding oracle.
    It uses the TRUE order (which must be provided or computed) and demonstrates the
    continued fractions recovery step.

    WARNING: This is NOT a factoring method - it requires knowing the order beforehand!
    Use this only for demonstrations and understanding Shor's full pipeline.

    Args:
        n: Number to factor
        a: Base (random if None)
        true_order: The actual order of a mod n (will compute if None, but that's cheating!)

    Returns:
        Tuple of (factor or None, diagnostic info)
    """
    n = mpz(n)

    if a is None:
        a = random.randint(2, int(n) - 2)
    a = mpz(a)

    diagnostics = {
        'mode': 'SIMULATED_QFT',
        'warning': 'This uses a hidden order oracle - not a real factoring method!',
        'a': int(a),
    }

    # If order not provided, we have to compute it (brute force for small n)
    if true_order is None:
        # This is the hard part that a quantum computer does efficiently!
        # We'll only do this for demonstration on small numbers
        if n > 10**9:
            diagnostics['error'] = 'Number too large for brute-force order finding'
            return None, diagnostics

        r = 1
        current = a
        while current != 1 and r < n:
            current = (current * a) % n
            r += 1

        if current != 1:
            diagnostics['error'] = 'Could not find order'
            return None, diagnostics

        true_order = r

    diagnostics['true_order'] = true_order
    diagnostics['order_source'] = 'provided_oracle' if true_order else 'brute_force'

    # Now apply Shor's classical post-processing
    factor = shor_classical_post_processing(a, true_order, n)

    if factor:
        diagnostics['success'] = True
        diagnostics['factor'] = int(factor)
    else:
        diagnostics['success'] = False
        diagnostics['reason'] = 'Unlucky case (order odd or a^(r/2) ≡ ±1)'

    return factor, diagnostics
