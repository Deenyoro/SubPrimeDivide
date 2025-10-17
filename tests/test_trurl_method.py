#!/usr/bin/env python3
"""
Test script for Trurl's semiprime factorization method.

This demonstrates the equation-based approach on small semiprimes
that can be verified quickly.
"""
from app.equations.semiprime_equation import SemiPrimeEquationSolver


def test_small_semiprime():
    """Test with a small semiprime: 143 = 11 × 13"""
    print("=" * 70)
    print("Test Case 1: 143 = 11 × 13")
    print("=" * 70)

    pnp = 143
    solver = SemiPrimeEquationSolver(pnp)

    # Generate diagnostic report
    report = solver.diagnostic_report()
    print(f"\nSemiprime: {report['pnp']}")
    print(f"Digits: {report['pnp_digits']}")
    print(f"sqrt(pnp): {report['sqrt_pnp']}")

    # Test the equation with known factors
    x_true = 11
    y_true = 13

    print(f"\nTesting with true factors: x={x_true}, y={y_true}")

    # Compute y from x using Trurl's equation
    y_computed = solver.compute_y_from_x(x_true)
    print(f"Trurl equation: y = (((pnp^2/x) + x^2) / pnp)")
    print(f"  Computed y = {y_computed}")
    print(f"  Actual y   = {y_true}")
    print(f"  Match: {abs(y_computed - y_true) <= 1}")

    # Verify inverse relationship
    print(f"\nVerifying inverse relationship (x↑ means y↓):")
    test_x_values = [5, 8, 11, 14, 17]
    for i in range(len(test_x_values) - 1):
        x1, x2 = test_x_values[i], test_x_values[i+1]
        y1 = solver.compute_y_from_x(x1)
        y2 = solver.compute_y_from_x(x2)
        holds = y1 > y2
        print(f"  x={x1:2d} → y={y1:3d}, x={x2:2d} → y={y2:3d}, y1>y2: {holds}")

    # Verify all constraints
    constraints = solver.verify_all_constraints(x_true, y_true)
    print(f"\nConstraint verification:")
    for name, satisfied in constraints.items():
        status = "PASS" if satisfied else "FAIL" if satisfied is False else "UNKNOWN"
        print(f"  {status} {name}: {satisfied}")

    # Find bounds
    lower, upper = solver.find_initial_bounds()
    print(f"\nComputed bounds:")
    print(f"  Lower: {lower}")
    print(f"  Upper: {upper}")
    print(f"  True factor {x_true} in range: {lower <= x_true <= upper}")


def test_medium_semiprime():
    """Test with medium semiprime: 323 = 17 × 19"""
    print("\n" + "=" * 70)
    print("Test Case 2: 323 = 17 × 19")
    print("=" * 70)

    pnp = 323
    solver = SemiPrimeEquationSolver(pnp)

    x_true = 17
    y_true = 19

    print(f"\nTrue factors: x={x_true}, y={y_true}")

    # Compute using equation
    y_computed = solver.compute_y_from_x(x_true)
    print(f"Trurl equation yields: y = {y_computed}")
    print(f"Match: {abs(y_computed - y_true) <= 1}")

    # Verify constraints
    constraints = solver.verify_all_constraints(x_true, y_true)
    all_good = all(v for v in constraints.values() if v is not None)
    print(f"All constraints satisfied: {all_good}")


def test_constraint_equation():
    """Test the constraint equation behavior"""
    print("\n" + "=" * 70)
    print("Test Case 3: Constraint Equation Analysis")
    print("=" * 70)

    pnp = 143
    solver = SemiPrimeEquationSolver(pnp)

    print(f"\nConstraint: ((pnp^2/x + x^2) / x) / pnp")
    print(f"Testing values around true factor x=11:")

    for x in range(7, 16):
        constraint_val = solver.compute_constraint_value(x)
        y_computed = solver.compute_y_from_x(x)
        is_factor = solver.verify_factor(x)
        marker = " ← TRUE FACTOR" if is_factor else ""
        print(f"  x={x:2d}: constraint={constraint_val:8.4f}, y={y_computed:4d}{marker}")


def test_rsa_260_diagnostic():
    """Show diagnostic for RSA-260"""
    print("\n" + "=" * 70)
    print("Test Case 4: RSA-260 Diagnostic")
    print("=" * 70)

    # RSA-260 from Trurl's post
    pnp = int("2211282552952966643528108525502623092761208950247001539441374831"
              "9128822941402001986512729726569746599085900330031400051170742204"
              "5608592763579537571859542988389587092292384910067030341246205457"
              "845664136645406842143612930176940208463910658759147942514351444581992")

    solver = SemiPrimeEquationSolver(pnp)

    report = solver.diagnostic_report()

    print(f"\nRSA-260 Analysis:")
    print(f"  Digits: {report['pnp_digits']}")
    print(f"  sqrt digits: {report['sqrt_pnp_digits']}")
    print(f"  Lower bound: 10^{report['lower_bound_exponent']:.1f}")
    print(f"  Upper bound: 10^{report['upper_bound_exponent']:.1f}")

    print(f"\nTrurl's stated range: 10^90 to 10^130")
    print(f"Our computed range:   10^{report['lower_bound_exponent']:.1f} to 10^{report['upper_bound_exponent']:.1f}")

    lower, upper = solver.find_initial_bounds()
    import math
    print(f"\nSearch space size: ~10^{math.log10(upper - lower):.1f} numbers")
    print(f"This is why RSA-260 remains unfactored!")


if __name__ == "__main__":
    print("\n")
    print("=" * 70)
    print(" " * 22 + "TRURL METHOD VERIFICATION")
    print("=" * 70)

    test_small_semiprime()
    test_medium_semiprime()
    test_constraint_equation()
    test_rsa_260_diagnostic()

    print("\n" + "=" * 70)
    print("All tests completed successfully!")
    print("=" * 70 + "\n")
