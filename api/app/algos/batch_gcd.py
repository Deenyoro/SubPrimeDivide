"""
Batch GCD Algorithm (Bernstein's algorithm)

Efficiently finds common factors among many numbers simultaneously.
This is orders of magnitude faster than computing pairwise GCDs.

Use case: When factoring multiple semiprimes, batch GCD can instantly
discover if any share a common prime factor (a catastrophic failure
in key generation, but useful for finding easy factorizations).

Time complexity: O(n log²n) for n numbers
Space complexity: O(n)

References:
- https://facthacks.cr.yp.to/batchgcd.html
- Bernstein, "How to find smooth parts of integers"
"""

import gmpy2
from typing import List, Dict, Tuple


def batch_gcd(numbers: List[int]) -> Dict[int, List[int]]:
    """
    Find common factors among a batch of numbers using Bernstein's algorithm.

    This is much faster than computing pairwise GCDs when you have many numbers.

    Args:
        numbers: List of numbers to analyze (typically semiprimes or composites)

    Returns:
        Dictionary mapping each input index to list of found factors.
        Only returns entries for numbers that have factors found.

    Example:
        >>> numbers = [143, 323, 437, 667]  # 11×13, 17×19, 19×23, 23×29
        >>> result = batch_gcd(numbers)
        >>> result
        {1: [19], 2: [19, 23], 3: [23]}  # Found shared primes 19 and 23
    """
    if not numbers:
        return {}

    n = len(numbers)

    # Convert to gmpy2.mpz for efficiency
    nums = [gmpy2.mpz(x) for x in numbers]

    # Build product tree
    product_tree = build_product_tree(nums)

    # Build remainder tree
    remainders = build_remainder_tree(product_tree, nums)

    # Extract factors
    results = {}
    for i, (num, remainder) in enumerate(zip(nums, remainders)):
        if remainder == 0:
            continue  # Shouldn't happen, but skip if it does

        # GCD of (original number) and (product/number mod number²)
        # This gives us any factors shared with other numbers
        factor = gmpy2.gcd(num * num // remainder, num)

        if factor > 1 and factor < num:
            # Found a non-trivial factor
            factors = factorize_completely(int(factor))
            results[i] = factors

    return results


def build_product_tree(numbers: List[gmpy2.mpz]) -> List[List[gmpy2.mpz]]:
    """
    Build a product tree for batch GCD.

    Each level contains products of pairs from the previous level.
    Level 0: original numbers
    Level 1: pairwise products
    Level 2: products of pairs from level 1
    ...
    Final level: product of all numbers

    Args:
        numbers: List of numbers as gmpy2.mpz

    Returns:
        List of levels, where each level is a list of products
    """
    tree = [numbers]

    while len(tree[-1]) > 1:
        prev_level = tree[-1]
        next_level = []

        # Multiply pairs
        for i in range(0, len(prev_level), 2):
            if i + 1 < len(prev_level):
                product = prev_level[i] * prev_level[i + 1]
            else:
                product = prev_level[i]
            next_level.append(product)

        tree.append(next_level)

    return tree


def build_remainder_tree(product_tree: List[List[gmpy2.mpz]],
                        numbers: List[gmpy2.mpz]) -> List[gmpy2.mpz]:
    """
    Build remainder tree from product tree.

    Starting from the root (product of all numbers), compute remainders
    at each level by taking modulo squares of numbers at that level.

    Args:
        product_tree: Product tree from build_product_tree
        numbers: Original numbers

    Returns:
        List of remainders, one for each original number
    """
    # Start with the root (product of all numbers)
    # We want to compute: (product of all other numbers) mod (n²) for each n

    # Begin with the full product at the top level
    if not product_tree or not product_tree[-1]:
        return []

    root = product_tree[-1][0]

    # Initialize remainder tree with root
    remainders = [[root]]

    # Work down the tree
    for level in range(len(product_tree) - 2, -1, -1):
        prev_remainders = remainders[-1]
        current_level = product_tree[level]
        next_remainders = []

        for i, remainder in enumerate(prev_remainders):
            # This remainder corresponds to a product of numbers at current level
            # Split it into two remainders for the children

            left_idx = i * 2
            right_idx = i * 2 + 1

            if left_idx < len(current_level):
                left_num = current_level[left_idx]
                left_remainder = remainder % (left_num * left_num)
                next_remainders.append(left_remainder)

            if right_idx < len(current_level):
                right_num = current_level[right_idx]
                right_remainder = remainder % (right_num * right_num)
                next_remainders.append(right_remainder)

        remainders.append(next_remainders)

    return remainders[-1]


def factorize_completely(n: int) -> List[int]:
    """
    Completely factorize a small number using trial division.

    This is used to extract all prime factors once batch GCD finds
    a composite factor.

    Args:
        n: Number to factorize (should be relatively small)

    Returns:
        List of prime factors (may contain duplicates)
    """
    factors = []
    n_mpz = gmpy2.mpz(n)

    # Trial division by small primes
    d = gmpy2.mpz(2)
    while d * d <= n_mpz:
        while n_mpz % d == 0:
            factors.append(int(d))
            n_mpz //= d

        if d == 2:
            d = 3
        else:
            d += 2

    if n_mpz > 1:
        factors.append(int(n_mpz))

    return factors


def batch_gcd_simple(numbers: List[int]) -> Dict[Tuple[int, int], int]:
    """
    Simple pairwise batch GCD (slower, but easier to understand).

    Computes GCD for all pairs and returns non-trivial common factors.

    Args:
        numbers: List of numbers

    Returns:
        Dictionary mapping (i, j) pairs to their GCD if GCD > 1

    Note:
        This is O(n²) and much slower than the tree-based algorithm.
        Use build_product_tree/build_remainder_tree for large batches.
    """
    results = {}
    n = len(numbers)

    for i in range(n):
        for j in range(i + 1, n):
            g = int(gmpy2.gcd(numbers[i], numbers[j]))
            if g > 1:
                results[(i, j)] = g

    return results


def preprocess_batch_for_factorization(numbers: List[int]) -> Dict[int, Dict[str, any]]:
    """
    Preprocess a batch of numbers before factorization.

    Uses batch GCD to find shared factors, then returns metadata
    for each number indicating what's already been factored.

    Args:
        numbers: List of semiprimes/composites to factor

    Returns:
        Dictionary with:
            - 'shared_factors': Factors found via batch GCD
            - 'remaining': Number after removing shared factors
            - 'trivial': True if fully factored by batch GCD

    Example:
        >>> numbers = [143, 323, 437]
        >>> result = preprocess_batch_for_factorization(numbers)
        >>> result[1]  # 323 = 17×19 shares factor 19 with 437 = 19×23
        {
            'shared_factors': [19],
            'remaining': 17,
            'trivial': False
        }
    """
    shared = batch_gcd(numbers)
    results = {}

    for i, n in enumerate(numbers):
        if i in shared:
            # Remove shared factors
            remaining = n
            for factor in shared[i]:
                while remaining % factor == 0:
                    remaining //= factor

            results[i] = {
                'shared_factors': shared[i],
                'remaining': remaining,
                'trivial': remaining == 1
            }
        else:
            results[i] = {
                'shared_factors': [],
                'remaining': n,
                'trivial': False
            }

    return results
