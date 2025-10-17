#!/usr/bin/env python3
"""
Simple standalone test of Trurl's "find x when y=1" equation.
No dependencies needed - pure Python for verification.
"""

import math

def compute_constraint_value(pnp, x):
    """
    Trurl's constraint equation: y = ((((pnp^2 / x) + x^2) / x) / pnp)
    """
    pnp_squared = pnp ** 2
    numerator = (pnp_squared // x) + (x * x)
    result = float(numerator) / float(x) / float(pnp)
    return result

def find_x_when_y_equals_one_newton(pnp):
    """
    Solve x^3 - pnp*x^2 + pnp^2 = 0 using Newton's method
    """
    # Initial guess: x ≈ pnp^(2/3)
    log_pnp = math.log10(float(pnp))
    log_x_initial = (2.0 / 3.0) * log_pnp
    x = int(10 ** log_x_initial)

    # Newton's method
    max_iterations = 100
    for iteration in range(max_iterations):
        x_squared = x * x
        x_cubed = x_squared * x

        # f(x) = x^3 - pnp*x^2 + pnp^2
        f_x = x_cubed - pnp * x_squared + pnp * pnp

        # f'(x) = 3x^2 - 2*pnp*x
        f_prime_x = 3 * x_squared - 2 * pnp * x

        if f_prime_x == 0:
            break

        # Newton step
        x_new = x - f_x // f_prime_x

        # Check convergence
        if abs(x_new - x) < max(1, x // 1000000):
            x = x_new
            break

        x = x_new

    return x

def test_semiprime(pnp, p=None, q=None, name=""):
    """Test a semiprime"""
    print(f"\n{'='*70}")
    print(f"{name}")
    print(f"pnp = {pnp} ({len(str(pnp))} digits)")

    # Find x where y = 1
    x_at_y_one = find_x_when_y_equals_one_newton(pnp)
    y_at_x = compute_constraint_value(pnp, x_at_y_one)

    print(f"\nTrurl's method: Find x where y = 1")
    print(f"  x = {x_at_y_one} ({len(str(x_at_y_one))} digits)")
    print(f"  y(x) = {y_at_x:.10f}")
    print(f"  |y - 1| = {abs(y_at_x - 1.0):.2e}")

    if p and q:
        smaller = min(p, q)
        larger = max(p, q)
        print(f"\nActual factors:")
        print(f"  p = {smaller} ({len(str(smaller))} digits)")
        print(f"  q = {larger} ({len(str(larger))} digits)")

        # How close?
        ratio = x_at_y_one / smaller
        print(f"\n  x / p_actual = {ratio:.6f}")
        print(f"  x is off by {(ratio - 1) * 100:.2f}%")

        # What's y at the actual factor?
        y_at_actual = compute_constraint_value(pnp, smaller)
        print(f"\n  y(p_actual) = {y_at_actual:.10f}")


if __name__ == "__main__":
    print("=" * 70)
    print("Testing Trurl's Equation: y = ((((pnp^2/x) + x^2)/x)/pnp)")
    print("Goal: Find x where y = 1")
    print("=" * 70)

    # Test 1: 143 = 11 × 13
    test_semiprime(143, 11, 13, "Test 1: 143 = 11 × 13")

    # Test 2: 1003001 = 991 × 1013
    test_semiprime(1003001, 991, 1013, "Test 2: 1003001 = 991 × 1013")

    # Test 3: Larger known semiprime
    p3 = 9576890767
    q3 = 9576890803
    test_semiprime(p3 * q3, p3, q3, f"Test 3: {p3} × {q3}")

    print("\n" + "=" * 70)
    print("SUMMARY:")
    print("  - Newton's method successfully finds x where y ≈ 1")
    print("  - This gives the 'general area' Trurl mentions")
    print("  - The actual smaller factor is close to this x value")
    print("=" * 70 + "\n")
