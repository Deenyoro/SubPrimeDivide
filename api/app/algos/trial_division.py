"""
Trial division with wheel factorization for efficient small factor finding
"""
import gmpy2
from primesieve import Iterator
from typing import Optional, Generator


def trial_division_with_wheel(n: int, limit: Optional[int] = None) -> Optional[int]:
    """
    Trial division using primesieve for fast prime generation.

    Args:
        n: Number to factor
        limit: Search up to this bound (default: min(10^9, sqrt(n)))

    Returns:
        Smallest prime factor found, or None

    This is only practical for finding small factors (< 10^9).
    For serious factorization, use ECM or GNFS.
    """
    if n % 2 == 0:
        return 2

    if limit is None:
        limit = min(10**9, int(gmpy2.isqrt(n)))

    # Use primesieve to generate primes efficiently
    it = Iterator()
    prime = it.next_prime()

    while prime <= limit:
        if n % prime == 0:
            return prime
        prime = it.next_prime()

    return None


def trial_division_range(
    n: int,
    start: int,
    end: int,
    callback=None,
    step: int = 100000
) -> Optional[int]:
    """
    Trial division over a specific range with progress callback.

    Args:
        n: Number to factor
        start: Start of range
        end: End of range
        callback: Function called periodically with (current, total)
        step: How often to call callback

    Returns:
        Factor found in range, or None
    """
    it = Iterator()
    it.skipto(start)

    count = 0
    total = end - start

    prime = it.next_prime()
    while prime <= end:
        if n % prime == 0:
            return prime

        count += 1
        if callback and count % step == 0:
            callback(prime - start, total)

        prime = it.next_prime()

    return None


def generate_primes_in_range(start: int, end: int) -> Generator[int, None, None]:
    """
    Generator yielding all primes in [start, end].

    Args:
        start: Start of range (inclusive)
        end: End of range (inclusive)

    Yields:
        Prime numbers in range
    """
    it = Iterator()
    it.skipto(start)

    prime = it.next_prime()
    while prime <= end:
        yield prime
        prime = it.next_prime()
