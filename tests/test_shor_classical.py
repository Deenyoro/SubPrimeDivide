#!/usr/bin/env python3
"""
Test script for Shor's classical emulation algorithm
"""
import sys
sys.path.insert(0, 'api')

from app.algos.shor_classical import shor_classical_one_shot, shor_classical_multi_attempt

def test_small_semiprimes():
    """Test with small semiprimes where we know the factors"""

    test_cases = [
        (143, 11, 13, "11 × 13"),
        (221, 13, 17, "13 × 17"),
        (1189, 29, 41, "29 × 41"),
        (3127, 53, 59, "53 × 59"),
        (10403, 101, 103, "101 × 103"),
    ]

    print("=" * 80)
    print("Testing Shor's Classical Emulation")
    print("=" * 80)
    print()

    for n, p, q, desc in test_cases:
        print(f"Test: n = {n} = {desc}")
        print("-" * 80)

        # Try single shot with default B
        factor, diag = shor_classical_one_shot(n, B=100000)

        if factor:
            cofactor = n // factor
            print(f"✓ SUCCESS: Found factor {factor}")
            print(f"  Cofactor: {cofactor}")
            print(f"  Verification: {factor} × {cofactor} = {factor * cofactor}")
            print(f"  Method: {diag.get('method')}")

            if 'order_found' in diag and diag['order_found']:
                print(f"  Order found: r = {diag['order_found']}")
                print(f"  Base used: a = {diag['a']}")

                if diag.get('shor_condition_satisfied'):
                    print(f"  Shor's conditions: ✓ (r even, a^(r/2) ≢ ±1 mod n)")
                else:
                    print(f"  Shor's conditions: ✗ ({diag.get('reason', 'unknown')})")
        else:
            print(f"✗ FAILED with single attempt (B=100000)")
            print(f"  Reason: {diag.get('reason', 'unknown')}")

            # Try multi-attempt
            print(f"  Trying multi-attempt with various B values...")
            factor_multi, all_diag = shor_classical_multi_attempt(n, max_attempts_per_B=5)

            if factor_multi:
                cofactor = n // factor_multi
                print(f"  ✓ Multi-attempt SUCCESS: Found factor {factor_multi}")
                print(f"    Verification: {factor_multi} × {cofactor} = {factor_multi * cofactor}")

                # Find successful attempt
                success_diag = [d for d in all_diag if d.get('method') and 'failed' not in d.get('method', '')]
                if success_diag:
                    d = success_diag[-1]
                    print(f"    Method: {d.get('method')}, B={d.get('B')}, a={d.get('a')}")
            else:
                print(f"  ✗ Multi-attempt also failed")
                print(f"    This semiprime may have orders that aren't smooth within tested bounds")

        print()

    print("=" * 80)


def test_edge_cases():
    """Test edge cases"""

    print("Testing Edge Cases")
    print("=" * 80)
    print()

    # Test with a prime (should fail)
    print("Test: n = 97 (prime)")
    factor, diag = shor_classical_one_shot(97, B=10000)
    if factor:
        print(f"  Unexpected factor found: {factor}")
    else:
        print(f"  ✓ Correctly identified as unfactorable (method: {diag.get('method')})")
    print()

    # Test with even number (should find factor 2 immediately)
    print("Test: n = 1234 (even)")
    factor, diag = shor_classical_one_shot(1234, B=10000)
    if factor == 2:
        print(f"  ✓ Found factor 2 via gcd check")
    else:
        print(f"  Factor: {factor}, method: {diag.get('method')}")
    print()

    print("=" * 80)


def test_order_finding_explanation():
    """Demonstrate the order-finding process"""

    print("Order-Finding Educational Demo")
    print("=" * 80)
    print()

    n = 143  # 11 × 13

    print(f"Factoring n = {n} = 11 × 13")
    print()
    print("Shor's algorithm steps:")
    print("1. Choose random a with gcd(a, n) = 1")
    print("2. Find order r of a mod n (smallest r > 0 where a^r ≡ 1 mod n)")
    print("3. If r is even and a^(r/2) ≢ ±1 mod n, compute gcd(a^(r/2) ± 1, n)")
    print()

    # Try with specific base for demonstration
    for a in [2, 3, 5, 7]:
        print(f"Trying a = {a}:")
        factor, diag = shor_classical_one_shot(n, B=100000, a=a)

        if diag.get('gcd_check') and diag['gcd_check'] > 1:
            print(f"  Lucky! gcd({a}, {n}) = {diag['gcd_check']} (trivial factor)")
        elif diag.get('order_found'):
            r = diag['order_found']
            print(f"  Order found: r = {r}")
            print(f"  r is {'even' if r % 2 == 0 else 'odd'}")

            if factor:
                print(f"  ✓ Factor extracted: {factor}")
                print(f"    Method: {diag.get('method')}")
            else:
                print(f"  ✗ Failed to extract factor")
                print(f"    Reason: {diag.get('reason')}")
        else:
            print(f"  Order not found (not smooth enough with B={diag.get('B')})")
        print()

    print("=" * 80)


if __name__ == "__main__":
    test_small_semiprimes()
    print("\n\n")
    test_edge_cases()
    print("\n\n")
    test_order_finding_explanation()
