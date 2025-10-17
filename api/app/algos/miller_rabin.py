"""
Miller-Rabin primality test implementation
https://en.wikipedia.org/wiki/Miller%E2%80%93Rabin_primality_test
"""
import gmpy2
from typing import Optional


def is_prime_mr(n: int, k: int = 40) -> bool:
    """
    Miller-Rabin primality test using gmpy2 for performance.

    Args:
        n: Number to test
        k: Number of rounds (higher = more certainty)

    Returns:
        True if n is probably prime, False if composite

    For k=40, error probability is < 2^-80 (negligible)
    """
    if n < 2:
        return False

    if n == 2 or n == 3:
        return True

    if n % 2 == 0:
        return False

    # Use gmpy2's built-in Miller-Rabin (optimized C implementation)
    return gmpy2.is_prime(n, k)


def next_prime(n: int) -> int:
    """Find the next prime after n"""
    return int(gmpy2.next_prime(n))


def probable_prime(bits: int) -> int:
    """Generate a random probable prime with given bit length"""
    state = gmpy2.random_state()
    return int(gmpy2.mpz_urandomb(state, bits))
