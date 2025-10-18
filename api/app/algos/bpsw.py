"""
Baillie-PSW Primality Test (BPSW)

Combines Miller-Rabin (base 2) with Lucas probable prime test.
No known counterexamples exist, making it deterministic for practical purposes.

References:
- https://en.wikipedia.org/wiki/Baillie%E2%80%93PSW_primality_test
- https://mathworld.wolfram.com/Baillie-PSWPrimalityTest.html
"""

import gmpy2


def is_prime_bpsw(n: int) -> bool:
    """
    Baillie-PSW primality test.

    Combines Miller-Rabin (base 2) with strong Lucas test.
    No known pseudoprimes to this test exist as of 2025.

    Args:
        n: Number to test

    Returns:
        True if n is (almost certainly) prime, False if composite

    Note:
        For n ≤ 2^64, this is deterministic (no known counterexamples).
        For larger n, this is a probable prime test with no known failures.
    """
    if n < 2:
        return False

    if n == 2:
        return True

    if n % 2 == 0:
        return False

    # Small primes check
    small_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
    if n in small_primes:
        return True

    # Quick divisibility check by small primes
    for p in small_primes:
        if n % p == 0:
            return False

    # Step 1: Miller-Rabin test with base 2
    if not miller_rabin_base2(n):
        return False

    # Step 2: Strong Lucas probable prime test
    if not strong_lucas_test(n):
        return False

    return True


def miller_rabin_base2(n: int) -> bool:
    """
    Miller-Rabin primality test with base 2.

    This is the first component of BPSW.
    """
    # gmpy2's is_prime with k=1 uses base 2
    return bool(gmpy2.is_prime(n, 1))


def strong_lucas_test(n: int) -> bool:
    """
    Strong Lucas probable prime test using Selfridge's method of choosing D, P, Q.

    This is the second component of BPSW.

    Algorithm:
    1. Find D using Selfridge's method: D is the first element of the sequence
       5, -7, 9, -11, 13, ... for which Jacobi(D, n) = -1
    2. Set P = 1, Q = (1 - D) / 4
    3. Perform the strong Lucas test with these parameters
    """
    # Convert to gmpy2.mpz for efficient arithmetic
    n_mpz = gmpy2.mpz(n)

    # Find D using Selfridge's method
    D = 5
    while True:
        jacobi = gmpy2.jacobi(D, n_mpz)

        if jacobi == 0:
            # D is a factor of n, so n is composite (unless D == n)
            return abs(D) == n

        if jacobi == -1:
            break

        # Next D in sequence: 5, -7, 9, -11, 13, -15, ...
        if D > 0:
            D = -(D + 2)
        else:
            D = -(D - 2)

        # Safety check: if we've searched too far, n might be a perfect square
        if abs(D) > 1000000:
            # Check if n is a perfect square
            sqrt_n = gmpy2.isqrt(n_mpz)
            if sqrt_n * sqrt_n == n_mpz:
                return False
            break

    # Set P = 1, Q = (1 - D) / 4
    P = 1
    Q = (1 - D) // 4

    # Perform strong Lucas test
    # Write n + 1 = 2^s * d where d is odd
    d = n_mpz + 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1

    # Compute Lucas sequence U_d and V_d
    U, V = lucas_sequence(n_mpz, P, Q, d)

    # Check if U_d ≡ 0 (mod n)
    if U % n_mpz == 0:
        return True

    # Check if V_{d*2^r} ≡ 0 (mod n) for some 0 ≤ r < s
    for r in range(s):
        if V % n_mpz == 0:
            return True

        # V_{2k} = V_k^2 - 2*Q^k (mod n)
        # Since we're doubling the subscript each time, Q^k becomes Q^{2k}
        V = (V * V - 2 * gmpy2.powmod(Q, d * (2 ** r), n_mpz)) % n_mpz

    return False


def lucas_sequence(n: int, P: int, Q: int, k: int) -> tuple[int, int]:
    """
    Compute Lucas sequences U_k and V_k modulo n using the binary method.

    U_k and V_k are defined by:
        U_0 = 0, U_1 = 1, U_k = P*U_{k-1} - Q*U_{k-2}
        V_0 = 2, V_1 = P, V_k = P*V_{k-1} - Q*V_{k-2}

    Args:
        n: Modulus
        P: Lucas parameter
        Q: Lucas parameter
        k: Index

    Returns:
        (U_k mod n, V_k mod n)
    """
    n_mpz = gmpy2.mpz(n)
    k_mpz = gmpy2.mpz(k)

    # Special cases
    if k == 0:
        return (0, 2)
    if k == 1:
        return (1, P)

    # Binary method for computing Lucas sequences
    # We use the doubling formulas:
    #   U_{2k} = U_k * V_k
    #   V_{2k} = V_k^2 - 2*Q^k
    #   U_{2k+1} = (P*U_{2k} + V_{2k}) / 2
    #   V_{2k+1} = (D*U_{2k} + P*V_{2k}) / 2
    # where D = P^2 - 4Q

    # Get binary representation of k
    bits = bin(k_mpz)[2:]  # Remove '0b' prefix

    # Start with U_1 = 1, V_1 = P
    U = gmpy2.mpz(1)
    V = gmpy2.mpz(P)
    Q_k = gmpy2.mpz(Q)

    # Process bits from second bit onward
    for bit in bits[1:]:
        # Double: compute U_{2k}, V_{2k}
        U_new = (U * V) % n_mpz
        V_new = (V * V - 2 * Q_k) % n_mpz
        Q_k = gmpy2.powmod(Q_k, 2, n_mpz)

        if bit == '1':
            # Add 1: compute U_{2k+1}, V_{2k+1}
            U = (P * U_new + V_new) % n_mpz
            V = (P * V_new + (P * P - 4 * Q) * U_new) % n_mpz

            # Ensure U and V are divided by 2 (since formulas have /2)
            if U % 2 == 1:
                U += n_mpz
            if V % 2 == 1:
                V += n_mpz

            U = U // 2
            V = V // 2

            Q_k = (Q_k * Q) % n_mpz
        else:
            U = U_new
            V = V_new

    return (int(U % n_mpz), int(V % n_mpz))


def is_prime_fast(n: int) -> bool:
    """
    Fast primality test that chooses the best method based on input size.

    - For n ≤ 2^64: Use BPSW (deterministic, no known counterexamples)
    - For n > 2^64: Use Miller-Rabin with k=40 rounds (probability of error < 2^-80)

    Args:
        n: Number to test

    Returns:
        True if n is (almost certainly) prime, False if composite
    """
    if n < 2:
        return False

    # For small numbers, use BPSW
    if n <= 2**64:
        return is_prime_bpsw(n)

    # For very large numbers, Miller-Rabin with 40 rounds is faster
    # and still has negligible error probability (< 2^-80)
    return bool(gmpy2.is_prime(n, 40))
