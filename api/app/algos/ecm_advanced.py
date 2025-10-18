"""
Advanced ECM (Elliptic Curve Method) using GMP-ECM system binary.

This provides industrial-strength ECM factorization for medium to large factors
(30-60 digits) that are too slow for Pollard-rho but faster than GNFS.
"""

import subprocess
import re
import shutil

# Check if ecm binary is available
HAS_ECM = shutil.which("ecm") is not None


def ecm_factor_advanced(n: int, B1: int = 1_000_000, curves: int = 1000, sigma: int = 0) -> int | None:
    """
    Use GMP-ECM to find a factor of n.

    Args:
        n: Number to factor
        B1: Stage 1 bound (larger = finds bigger factors, but slower)
        curves: Number of elliptic curves to try
        sigma: Random seed (0 = random)

    Returns:
        A non-trivial factor if found, None otherwise

    Typical B1 values:
        - 30-digit factors: B1 = 11_000
        - 35-digit factors: B1 = 50_000
        - 40-digit factors: B1 = 250_000
        - 45-digit factors: B1 = 1_000_000
        - 50-digit factors: B1 = 3_000_000
        - 55-digit factors: B1 = 11_000_000
        - 60-digit factors: B1 = 43_000_000
    """
    if not HAS_ECM:
        return None

    if n <= 1:
        return None

    try:
        # Build ECM command
        cmd = ["ecm", "-c", str(curves)]
        if sigma > 0:
            cmd.extend(["-sigma", str(sigma)])
        cmd.append(str(B1))

        # Run ECM with the number as input
        result = subprocess.run(
            cmd,
            input=str(n),
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout per ECM run
        )

        # Parse output for factors
        # ECM outputs: "Found prime factor of <n> digits: <factor>"
        # or: "Found composite factor of <n> digits: <factor>"
        output = result.stdout + result.stderr

        # Look for factor pattern
        factor_pattern = r"(?:prime|composite) factor of \d+ digits?: (\d+)"
        match = re.search(factor_pattern, output)

        if match:
            factor = int(match.group(1))
            if 1 < factor < n:
                return factor

        return None

    except subprocess.TimeoutExpired:
        print(f"ECM timed out after 1 hour")
        return None
    except Exception as e:
        print(f"ECM error: {e}")
        return None


def ecm_factor_staged_advanced(n: int, digit_count: int, callback=None) -> int | None:
    """
    Run ECM with staged B1 bounds appropriate for the expected factor size.

    Args:
        n: Number to factor
        digit_count: Number of digits in n (determines strategy)
        callback: Optional function(stage, total_stages, B1, curves) for progress

    Returns:
        A factor if found, None otherwise
    """
    if not HAS_ECM:
        return None

    # Strategy based on composite size
    # For balanced semiprimes, factor size ≈ n^0.5 ≈ digit_count / 2
    expected_factor_digits = digit_count // 2

    # ECM stages: (B1, curves)
    # Start conservative, escalate if needed
    if expected_factor_digits <= 20:
        # Small factors - use basic ECM
        stages = [
            (11_000, 100),      # 30-digit factors
            (50_000, 200),      # 35-digit factors
        ]
    elif expected_factor_digits <= 30:
        # Medium factors
        stages = [
            (50_000, 200),      # 35-digit factors
            (250_000, 500),     # 40-digit factors
            (1_000_000, 1000),  # 45-digit factors
        ]
    elif expected_factor_digits <= 40:
        # Larger factors - more aggressive
        stages = [
            (250_000, 500),     # 40-digit factors
            (1_000_000, 2000),  # 45-digit factors
            (3_000_000, 4000),  # 50-digit factors
        ]
    else:
        # Very large - ECM is a long shot but worth trying
        stages = [
            (1_000_000, 1000),   # 45-digit factors
            (3_000_000, 2000),   # 50-digit factors
            (11_000_000, 4000),  # 55-digit factors
            (43_000_000, 8000),  # 60-digit factors
        ]

    total_stages = len(stages)

    for stage_num, (B1, curves) in enumerate(stages):
        if callback:
            callback(stage_num, total_stages, B1, curves)

        factor = ecm_factor_advanced(n, B1=B1, curves=curves)
        if factor:
            return factor

    return None


def suggest_ecm_params(digit_count: int) -> dict:
    """
    Suggest ECM parameters based on the size of the number.

    Returns:
        Dictionary with recommended B1, curves, and estimated time
    """
    expected_factor_digits = digit_count // 2

    if expected_factor_digits <= 30:
        return {
            'B1': 50_000,
            'curves': 200,
            'expected_time': '1-10 minutes',
            'success_probability': 'High for 35-digit factors'
        }
    elif expected_factor_digits <= 40:
        return {
            'B1': 1_000_000,
            'curves': 2000,
            'expected_time': '30 minutes - 2 hours',
            'success_probability': 'Good for 45-digit factors'
        }
    elif expected_factor_digits <= 50:
        return {
            'B1': 3_000_000,
            'curves': 4000,
            'expected_time': '2-12 hours',
            'success_probability': 'Moderate for 50-digit factors'
        }
    else:
        return {
            'B1': 11_000_000,
            'curves': 8000,
            'expected_time': '1-7 days',
            'success_probability': 'Low for 55+ digit factors (GNFS recommended)'
        }
