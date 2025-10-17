"""
Wrapper for GMP-ECM (Elliptic Curve Method)
https://en.wikipedia.org/wiki/Lenstra_elliptic-curve_factorization
"""
import subprocess
import re
from typing import Optional, Tuple
import gmpy2


def ecm_factor(n: int, B1: int = 50000, curves: int = 100) -> Optional[int]:
    """
    Use GMP-ECM to find factors via elliptic curve method.

    Args:
        n: Number to factor
        B1: Stage 1 bound (higher = more powerful, slower)
        curves: Number of curves to try

    Returns:
        A non-trivial factor if found, else None

    ECM is excellent for finding factors up to ~30-40 digits.
    Larger B1 and more curves increase success probability.
    """
    if gmpy2.is_prime(n):
        return None

    if n % 2 == 0:
        return 2

    try:
        # Call external ecm binary
        # Format: ecm -c <curves> <B1> <<< "<n>"
        result = subprocess.run(
            ['ecm', '-c', str(curves), str(B1)],
            input=str(n),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per ECM attempt
        )

        # Parse output for factors
        # ECM outputs lines like: "********** Factor found in step 1: 12345"
        for line in result.stdout.split('\n'):
            if 'Factor found' in line:
                match = re.search(r':\s*(\d+)', line)
                if match:
                    factor = int(match.group(1))
                    if 1 < factor < n:
                        return factor

        return None

    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        # ECM not installed, skip
        return None
    except Exception as e:
        print(f"ECM error: {e}")
        return None


def ecm_factor_staged(
    n: int,
    stages: list[Tuple[int, int]] = None,
    callback=None
) -> Optional[int]:
    """
    Run ECM in stages with increasing difficulty.

    Args:
        n: Number to factor
        stages: List of (B1, curves) tuples. Default is [(1e4,25), (5e4,100), (25e4,200)]
        callback: Function called after each stage with (stage_num, total_stages, factor_found)

    Returns:
        First non-trivial factor found, or None
    """
    if stages is None:
        stages = [
            (10000, 25),      # Quick pass
            (50000, 100),     # Standard
            (250000, 200),    # Deep search
        ]

    for i, (B1, curves) in enumerate(stages):
        if callback:
            callback(i, len(stages), None)

        factor = ecm_factor(n, B1, curves)

        if factor:
            if callback:
                callback(i, len(stages), factor)
            return factor

    return None
