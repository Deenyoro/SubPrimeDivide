#!/usr/bin/env python3
"""
Test script for Trurl's "find x when y=1" method.

Tests the equation: y = ((((pnp^2 / x) + x^2) / x) / pnp)
Finding x where y = 1
"""

import sys
sys.path.insert(0, '/opt/docker/SemiPrimeDivide/api')

from app.equations.semiprime_equation import SemiPrimeEquationSolver

def test_semiprime(pnp, expected_p=None, expected_q=None, name=""):
    """Test a semiprime with Trurl's method"""
    print(f"\n{'='*80}")
    print(f"Testing: {name}")
    print(f"pnp = {pnp}")
    print(f"pnp digits = {len(str(pnp))}")

    solver = SemiPrimeEquationSolver(pnp)

    # Find x where y = 1
    x_at_y_one = solver.find_x_when_y_equals_one()
    print(f"\nTrurl's method - x where y=1:")
    print(f"  x = {x_at_y_one}")
    print(f"  x digits = {len(str(x_at_y_one))}")

    # Verify by computing y at this x
    y_computed = solver.compute_constraint_value(x_at_y_one)
    print(f"  y (constraint eq) = {y_computed:.10f}")
    print(f"  Is y ≈ 1? {abs(y_computed - 1.0) < 0.01}")

    # Compare to actual factors if known
    if expected_p and expected_q:
        smaller = min(expected_p, expected_q)
        larger = max(expected_p, expected_q)

        print(f"\nActual factors:")
        print(f"  p = {smaller}")
        print(f"  q = {larger}")
        print(f"  p digits = {len(str(smaller))}")
        print(f"  q digits = {len(str(larger))}")

        # How close is x_at_y_one to the actual smaller factor?
        import math
        ratio = x_at_y_one / smaller
        log_ratio = math.log10(ratio) if ratio > 0 else 0

        print(f"\nComparison to actual p:")
        print(f"  x / p = {ratio:.6f}")
        print(f"  log10(x/p) = {log_ratio:.6f}")
        print(f"  x is {ratio:.2f}x the actual factor")

        # Test constraint equation at actual factor
        y_at_actual = solver.compute_constraint_value(smaller)
        print(f"\nConstraint equation at actual factor p:")
        print(f"  y = {y_at_actual:.10f}")

    # Get bounds using current find_initial_bounds
    lower, upper = solver.find_initial_bounds()
    print(f"\nCurrent find_initial_bounds():")
    print(f"  lower = 10^{len(str(lower))-1} (approx)")
    print(f"  upper = 10^{len(str(upper))-1} (approx)")

    if expected_p and expected_q:
        smaller = min(expected_p, expected_q)
        in_range = lower <= smaller <= upper
        print(f"  Actual factor in range? {in_range}")


if __name__ == "__main__":
    print("Trurl's Method: Find x where y = 1")
    print("Equation: y = ((((pnp^2 / x) + x^2) / x) / pnp)")

    # Test 1: Simple semiprime 143 = 11 × 13
    test_semiprime(143, 11, 13, "Simple: 143 = 11 × 13")

    # Test 2: Medium semiprime 1003001 = 991 × 1013
    test_semiprime(1003001, 991, 1013, "Medium: 1003001 = 991 × 1013")

    # Test 3: Larger semiprime (100 digits)
    # RSA-100 factors (known)
    p_rsa100 = 37975227936943673922808872755445627854565536638199
    q_rsa100 = 40094690950920881030683735292761468389214899724061
    pnp_rsa100 = p_rsa100 * q_rsa100
    test_semiprime(pnp_rsa100, p_rsa100, q_rsa100, "RSA-100")

    # Test 4: RSA-260 (unknown factors)
    rsa_260 = int("221128255295296664352810852550262309276120895024"
                  "700153944137483191288229414020019865127297265697"
                  "465990859003300314000511707422045608592763579537"
                  "571859544298838958709229238491006703034124620545"
                  "784566413664540684214361293017694020846391065875"
                  "914794251435144458199")
    test_semiprime(rsa_260, None, None, "RSA-260 (unfactored)")

    print(f"\n{'='*80}\n")
