"""
Mathematical Analysis of Trurl's Semiprime Equations

This module provides rigorous mathematical analysis and derivations
for the equation-based factorization approach.
"""
import gmpy2
from typing import Tuple, List, Dict
import math
from decimal import Decimal, getcontext


class TrurlEquationAnalysis:
    """
    Deep mathematical analysis of Trurl's equations.

    This class explores the theoretical underpinnings and provides
    rigorous justification for the method.
    """

    def __init__(self, pnp: int):
        """
        Initialize analysis for a semiprime.

        Args:
            pnp: The semiprime N = p * q
        """
        self.pnp = gmpy2.mpz(pnp)
        self.sqrt_pnp = gmpy2.isqrt(self.pnp)
        getcontext().prec = max(300, len(str(pnp)) + 200)

    def primary_equation_analysis(self, x: int) -> Dict:
        """
        Analyze the primary Trurl equation: y = (((pnp^2/x) + x^2) / pnp)

        Mathematical derivation:
        Given pnp = x * y (true factorization), let's see what the equation yields:

        y_computed = (pnp^2/x + x^2) / pnp

        Substituting pnp = x * y_true:
        y_computed = ((x*y)^2/x + x^2) / (x*y)
                   = (x*y^2 + x^2) / (x*y)
                   = x(y^2 + x) / (x*y)
                   = (y^2 + x) / y
                   = y + x/y

        So when x is the TRUE smaller factor:
        y_computed ≈ y_true   (error term is x/y which is small when y >> x)

        Args:
            x: Test value for smaller factor

        Returns:
            Dictionary with analysis results
        """
        x = gmpy2.mpz(x)

        # Compute using the equation
        term1 = self.pnp ** 2 // x  # pnp^2 / x
        term2 = x ** 2               # x^2
        numerator = term1 + term2    # (pnp^2/x + x^2)
        y_computed = numerator // self.pnp

        # If x actually divides pnp, compute the true y
        if self.pnp % x == 0:
            y_true = self.pnp // x
            error = y_computed - y_true

            # Theoretical error should be approximately x/y
            theoretical_error = x / y_true if y_true > 0 else 0

            return {
                'x': int(x),
                'y_computed': int(y_computed),
                'y_true': int(y_true),
                'error': int(error),
                'theoretical_error': float(theoretical_error),
                'error_relative': float(error) / float(y_true) if y_true > 0 else 0,
                'is_exact_factor': True
            }
        else:
            return {
                'x': int(x),
                'y_computed': int(y_computed),
                'y_true': None,
                'error': None,
                'theoretical_error': None,
                'is_exact_factor': False
            }

    def constraint_equation_analysis(self, x: int) -> Dict:
        """
        Analyze the constraint equation: ((pnp^2/x + x^2) / x) / pnp

        Mathematical simplification:
        ((pnp^2/x + x^2) / x) / pnp
        = (pnp^2/(x*x) + x^2/x) / pnp
        = (pnp^2/x^2 + x) / pnp

        For true factors where pnp = x*y:
        = ((x*y)^2/x^2 + x) / (x*y)
        = (y^2 + x) / (x*y)
        = y^2/(x*y) + x/(x*y)
        = y/x + 1/y

        This is the ratio of y/x plus a small correction term 1/y.

        For balanced semiprimes (y ≈ x ≈ sqrt(pnp)):
        constraint ≈ 1 + 1/sqrt(pnp) ≈ 1

        For unbalanced semiprimes (y >> x):
        constraint ≈ y/x (large value)

        Args:
            x: Test value

        Returns:
            Analysis of constraint value
        """
        x = gmpy2.mpz(x)

        # Compute constraint value
        numerator = self.pnp ** 2 // (x * x) + x
        constraint_value = float(numerator) / float(self.pnp)

        result = {
            'x': int(x),
            'constraint_value': constraint_value,
        }

        # If x is a true factor, compute theoretical value
        if self.pnp % x == 0:
            y_true = self.pnp // x
            theoretical_value = float(y_true) / float(x) + 1.0 / float(y_true)
            result['y_true'] = int(y_true)
            result['theoretical_constraint'] = theoretical_value
            result['ratio_y_over_x'] = float(y_true) / float(x)
            result['correction_term'] = 1.0 / float(y_true)

        return result

    def inverse_relationship_proof(self, x1: int, x2: int) -> Dict:
        """
        Prove mathematically that the inverse relationship holds.

        For the equation y = (pnp^2/x + x^2) / pnp, we want to show:
        If x1 < x2, then y1 > y2

        Let f(x) = (pnp^2/x + x^2) / pnp

        Taking the derivative:
        f'(x) = (-pnp^2/x^2 + 2x) / pnp
              = (2x - pnp^2/x^2) / pnp
              = (2x^3 - pnp^2) / (pnp * x^2)

        f'(x) < 0 when 2x^3 < pnp^2
                  when x^3 < pnp^2/2
                  when x < (pnp^2/2)^(1/3)

        For x < (pnp^2/2)^(1/3), the function is decreasing.
        So for x in the search range (below this critical point), y decreases as x increases.

        Args:
            x1: Smaller x value
            x2: Larger x value

        Returns:
            Analysis proving or disproving inverse relationship
        """
        x1, x2 = gmpy2.mpz(x1), gmpy2.mpz(x2)

        # Compute y values
        y1 = (self.pnp ** 2 // x1 + x1 ** 2) // self.pnp
        y2 = (self.pnp ** 2 // x2 + x2 ** 2) // self.pnp

        # Critical point where derivative changes sign
        critical_x_cubed = self.pnp ** 2 // 2
        # This would be critical_x = critical_x_cubed^(1/3), but for huge numbers
        # we can check if x is below it by comparing x^3 to pnp^2/2

        x1_cubed = x1 ** 3
        x2_cubed = x2 ** 3

        return {
            'x1': int(x1),
            'x2': int(x2),
            'y1': int(y1),
            'y2': int(y2),
            'y1_greater_than_y2': y1 > y2,
            'inverse_holds': y1 > y2,
            'x1_below_critical': x1_cubed < critical_x_cubed,
            'x2_below_critical': x2_cubed < critical_x_cubed,
            'both_in_decreasing_region': (x1_cubed < critical_x_cubed and
                                          x2_cubed < critical_x_cubed),
            'critical_point_exponent': math.log10(float(critical_x_cubed)) / 3.0
                                       if critical_x_cubed > 0 else 0
        }

    def optimal_search_range_theory(self) -> Dict:
        """
        Theoretical analysis of optimal search range.

        For a semiprime pnp = p * q where p <= q:
        - Trivially: p <= sqrt(pnp) <= q
        - Upper bound: sqrt(pnp)

        For the lower bound, we need heuristics based on the type of semiprime:

        1. Balanced semiprime (p ≈ q ≈ sqrt(pnp)):
           - p is close to sqrt(pnp)
           - Lower bound can be tight: perhaps sqrt(pnp)/10

        2. Unbalanced semiprime (p << q):
           - p could theoretically be as small as 2
           - For RSA-type numbers, factors are chosen to be large
           - Empirical lower bound: 10^(d/3) where d = digits in pnp

        3. The Trurl heuristic for RSA-260:
           - pnp has 260 digits
           - Suggests lower bound ≈ 10^90 ≈ 10^(260/3)
           - This assumes factors are somewhat balanced

        Returns:
            Theoretical bounds analysis
        """
        digits = len(str(self.pnp))
        sqrt_pnp = self.sqrt_pnp

        # Upper bound: always sqrt(pnp)
        upper_bound = sqrt_pnp

        # Lower bound heuristics
        # Heuristic 1: 10^(d/3) - very conservative
        lower_h1_exp = digits // 3
        lower_h1 = gmpy2.mpz(10) ** lower_h1_exp

        # Heuristic 2: 10^(d * 0.35) - slightly more aggressive (matches Trurl for RSA-260)
        lower_h2_exp = int(digits * 0.35)
        lower_h2 = gmpy2.mpz(10) ** lower_h2_exp

        # Heuristic 3: sqrt(pnp) / 10^k for some k
        # For balanced, k might be 1-2; for very unbalanced, k could be large
        lower_h3_exp = int(math.log10(float(sqrt_pnp))) - 30  # 30 digit reduction
        lower_h3 = gmpy2.mpz(10) ** lower_h3_exp if lower_h3_exp > 0 else gmpy2.mpz(2)

        return {
            'pnp_digits': digits,
            'sqrt_pnp_digits': len(str(sqrt_pnp)),
            'upper_bound': int(upper_bound),
            'upper_bound_exponent': math.log10(float(upper_bound)),
            'lower_heuristic_1': {
                'value': int(lower_h1),
                'exponent': lower_h1_exp,
                'description': '10^(d/3) - very conservative'
            },
            'lower_heuristic_2': {
                'value': int(lower_h2),
                'exponent': lower_h2_exp,
                'description': '10^(d*0.35) - Trurl RSA-260 match'
            },
            'lower_heuristic_3': {
                'value': int(lower_h3),
                'exponent': lower_h3_exp,
                'description': 'sqrt(pnp) / 10^30'
            },
            'recommended_lower': int(lower_h2),
            'recommended_lower_exponent': lower_h2_exp,
            'search_space_exponent': math.log10(float(upper_bound - lower_h2))
        }

    def equation_behavior_at_sqrt(self) -> Dict:
        """
        Analyze equation behavior at x = sqrt(pnp).

        For a balanced semiprime where p ≈ q ≈ sqrt(pnp):

        y_computed = (pnp^2/sqrt(pnp) + (sqrt(pnp))^2) / pnp
                   = (pnp^(3/2) + pnp) / pnp
                   = sqrt(pnp) + 1

        So at the square root, y_computed ≈ sqrt(pnp).

        Returns:
            Analysis at the critical sqrt point
        """
        x = self.sqrt_pnp

        y_computed = (self.pnp ** 2 // x + x ** 2) // self.pnp

        return {
            'x': int(x),
            'sqrt_pnp': int(self.sqrt_pnp),
            'y_computed': int(y_computed),
            'ratio_y_to_x': float(y_computed) / float(x) if x > 0 else 0,
            'difference_y_minus_x': int(y_computed - x),
            'interpretation': 'For balanced semiprime, y ≈ x ≈ sqrt(pnp)'
        }

    def numerical_stability_analysis(self, x_values: List[int]) -> List[Dict]:
        """
        Analyze numerical stability of the equations for various x values.

        The equations involve pnp^2 which can be enormous for large semiprimes.
        We need to ensure integer arithmetic doesn't overflow and that
        division results are accurate.

        Args:
            x_values: List of x values to test

        Returns:
            List of stability analyses
        """
        results = []

        for x in x_values:
            x = gmpy2.mpz(x)

            # Check magnitude of terms
            pnp_squared = self.pnp ** 2
            term1 = pnp_squared // x
            term2 = x ** 2

            # Relative magnitudes
            if term1 > 0:
                ratio = float(term2) / float(term1) if term1 > 0 else float('inf')
            else:
                ratio = float('inf')

            results.append({
                'x': int(x),
                'pnp_squared_digits': len(str(pnp_squared)),
                'term1_pnp2_over_x_digits': len(str(term1)),
                'term2_x_squared_digits': len(str(term2)),
                'term2_over_term1_ratio': ratio,
                'dominant_term': 'pnp^2/x' if ratio < 1 else 'x^2',
                'numerically_stable': True  # gmpy2 handles arbitrary precision
            })

        return results

    def comprehensive_report(self) -> Dict:
        """
        Generate a comprehensive mathematical analysis report.

        Returns:
            Complete analysis of the Trurl method for this semiprime
        """
        # Test points for analysis
        sqrt_val = int(self.sqrt_pnp)
        test_points = [
            sqrt_val // 1000,
            sqrt_val // 100,
            sqrt_val // 10,
            sqrt_val,
        ]

        return {
            'semiprime_properties': {
                'value': str(self.pnp)[:50] + '...' if len(str(self.pnp)) > 50 else str(self.pnp),
                'digits': len(str(self.pnp)),
                'sqrt_digits': len(str(self.sqrt_pnp)),
            },
            'primary_equation': self.primary_equation_analysis(sqrt_val),
            'constraint_equation': self.constraint_equation_analysis(sqrt_val),
            'inverse_relationship': self.inverse_relationship_proof(
                test_points[0], test_points[1]
            ),
            'search_range': self.optimal_search_range_theory(),
            'sqrt_behavior': self.equation_behavior_at_sqrt(),
            'numerical_stability': self.numerical_stability_analysis(test_points),
        }
