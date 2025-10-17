"""
Pollard's Rho algorithm for integer factorization (Brent's variant)
https://en.wikipedia.org/wiki/Pollard%27s_rho_algorithm
"""
import gmpy2
from typing import Optional
import random


def pollard_rho(n: int, max_iterations: int = 1000000) -> Optional[int]:
    """
    Pollard's Rho algorithm using Brent's cycle detection.

    Args:
        n: Number to factor
        max_iterations: Maximum iterations before giving up

    Returns:
        A non-trivial factor of n, or None if none found

    This is a probabilistic algorithm that often finds small factors quickly.
    For large composites, it may fail or take too long.
    """
    if n % 2 == 0:
        return 2

    if gmpy2.is_prime(n):
        return None

    # Random starting values
    x = random.randint(2, n - 2)
    y = x
    c = random.randint(1, n - 1)
    d = 1

    # Brent's improvement: exponentially growing step sizes
    power = lam = 1

    for _ in range(max_iterations):
        if power == lam:
            y = x
            power *= 2
            lam = 0

        # Polynomial function f(x) = (x^2 + c) mod n
        x = (gmpy2.powmod(x, 2, n) + c) % n
        lam += 1

        d = gmpy2.gcd(abs(x - y), n)

        if d != 1:
            if d == n:
                # Failure, restart with different params
                return pollard_rho(n, max_iterations // 2)
            return int(d)

    return None


def pollard_rho_with_callback(n: int, callback=None, max_iterations: int = 1000000) -> Optional[int]:
    """
    Pollard's Rho with progress callback for long-running jobs.

    Args:
        n: Number to factor
        callback: Function called periodically with (iteration, max_iterations)
        max_iterations: Maximum iterations before giving up

    Returns:
        A non-trivial factor of n, or None if none found
    """
    if n % 2 == 0:
        return 2

    if gmpy2.is_prime(n):
        return None

    x = random.randint(2, n - 2)
    y = x
    c = random.randint(1, n - 1)
    d = 1

    power = lam = 1

    for i in range(max_iterations):
        if callback and i % 10000 == 0:
            callback(i, max_iterations)

        if power == lam:
            y = x
            power *= 2
            lam = 0

        x = (gmpy2.powmod(x, 2, n) + c) % n
        lam += 1

        d = gmpy2.gcd(abs(x - y), n)

        if d != 1:
            if d == n:
                return pollard_rho_with_callback(n, callback, max_iterations // 2)
            return int(d)

    return None
