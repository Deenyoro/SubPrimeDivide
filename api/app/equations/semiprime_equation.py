"""
Trurl's Semiprime Factorization Method

Based on the observation that for a semiprime pnp = x * y, the equation
y = (((pnp^2/x) + x^2) / pnp) exhibits specific properties that bound the
smaller factor x.

Key insights from Trurl:
1. The equation y = (((pnp^2/x) + x^2) / pnp) relates x and y factors
2. When graphed, where y=0 gives the approximate location of the smaller factor
3. There's an inverse relationship: as x increases, y decreases (and vice versa)
4. The constraint equation (((pnp^2/x) + x^2) / x) / pnp helps identify bounds
5. For RSA-260, this narrows the search to approximately 10^90 to 10^130

Reference: Trurl's post on Mathematics forum, Nov 23
"""
import gmpy2
from typing import Optional, Tuple, Dict
from decimal import Decimal, getcontext
import math


class SemiPrimeEquationSolver:
    """
    Implementation of Trurl's equation-based semiprime factorization.

    Given pnp = x * y (where x <= y are prime factors), this solver uses
    the equation y = (((pnp^2/x) + x^2) / pnp) to establish search bounds.
    """

    def __init__(self, pnp: int):
        """
        Initialize solver for a semiprime.

        Args:
            pnp: The semiprime (product of two primes)
        """
        self.pnp = gmpy2.mpz(pnp)
        self.pnp_squared = self.pnp ** 2
        self.sqrt_pnp = gmpy2.isqrt(self.pnp)

        # High precision for floating-point bound calculations
        getcontext().prec = max(200, len(str(pnp)) + 100)

    def compute_y_from_x(self, x: int) -> int:
        """
        Primary Trurl equation: y = (((pnp^2/x) + x^2) / pnp)

        This equation relates the two factors. When x is the true smaller
        factor, computing y via this equation should yield the larger factor.

        Args:
            x: Candidate for smaller factor

        Returns:
            Computed y value
        """
        x = gmpy2.mpz(x)
        # Compute: (pnp^2 / x) + x^2
        term1 = self.pnp_squared // x
        term2 = x * x
        numerator = term1 + term2

        # Divide by pnp
        y = numerator // self.pnp
        return int(y)

    def compute_constraint_value(self, x: int) -> float:
        """
        Constraint equation: ((pnp^2/x + x^2) / x) / pnp

        Trurl notes this helps identify where "y = 0" on the graph, which
        approximates the location of the smaller factor.

        Args:
            x: Test value

        Returns:
            Constraint value (examining where this approaches specific values)
        """
        x = gmpy2.mpz(x)
        # (pnp^2 / x) + x^2
        numerator = (self.pnp_squared // x) + (x * x)
        # Divide by x, then by pnp using high-precision arithmetic
        result_mpz = numerator // x // self.pnp
        # For the fractional part, use Decimal for precision
        try:
            result = float(result_mpz)
        except:
            # For extremely large numbers, use logarithmic approximation
            log_num = len(str(numerator))
            log_x = len(str(x))
            log_pnp = len(str(self.pnp))
            approx_log = log_num - log_x - log_pnp
            result = 10.0 ** approx_log if approx_log < 300 else float('inf')
        return result

    def verify_inverse_relationship(self, x1: int, x2: int) -> bool:
        """
        Verify Trurl's key observation: x increases → y decreases.

        For x1 < x2, we should have y1 > y2 (inverse relationship).

        Args:
            x1: Smaller test value
            x2: Larger test value

        Returns:
            True if inverse relationship holds
        """
        if x1 >= x2:
            return False

        y1 = self.compute_y_from_x(x1)
        y2 = self.compute_y_from_x(x2)

        return y1 > y2

    def find_critical_point_derivative(self) -> int:
        """
        Find the critical point where the primary equation's derivative changes sign.

        Mathematical analysis:
        For f(x) = (pnp^2/x + x^2) / pnp, the derivative is:

        f'(x) = (-pnp^2/x^2 + 2x) / pnp
              = (2x^3 - pnp^2) / (pnp * x^2)

        f'(x) = 0 when:
        2x^3 - pnp^2 = 0
        x^3 = pnp^2/2
        x = (pnp^2/2)^(1/3)

        For x < critical_x: f'(x) < 0 (decreasing, inverse relationship holds)
        For x > critical_x: f'(x) > 0 (increasing, inverse relationship fails)

        Returns:
            Critical x value where derivative changes sign
        """
        # x_critical = (pnp^2 / 2)^(1/3)
        # For numerical stability with huge numbers, we use:
        # x_critical = pnp^(2/3) / 2^(1/3)

        # Compute pnp^(2/3) using logarithms for huge numbers
        # Use string length for log10 approximation to avoid float overflow
        import math
        pnp_digits = len(str(self.pnp))
        log_pnp = pnp_digits - 1  # Approximation
        log_critical = (2.0 / 3.0) * log_pnp - math.log10(2.0) / 3.0

        # Convert back
        critical_x = gmpy2.mpz(10) ** int(log_critical)

        return int(critical_x)

    def verify_decreasing_region(self, x: int) -> bool:
        """
        Verify that x is in the decreasing region (where inverse relationship holds).

        The function is decreasing when x^3 < pnp^2/2.

        Args:
            x: Test value

        Returns:
            True if x is in the region where inverse relationship holds
        """
        x_cubed = gmpy2.mpz(x) ** 3
        threshold = self.pnp_squared // 2

        return x_cubed < threshold

    def find_x_when_y_equals_one(self) -> int:
        """
        Find x where Trurl's constraint equation equals 1.

        Trurl's actual equation: y = ((((pnp^2 / x) + x^2) / x) / pnp)

        "Find x on graph where y on graph equals 1"

        Setting y = 1 and solving:
        ((pnp^2/x + x^2) / x) / pnp = 1
        (pnp^2/x + x^2) / x = pnp
        pnp^2/x + x^2 = pnp * x
        pnp^2 + x^3 = pnp * x^2
        x^3 - pnp*x^2 + pnp^2 = 0

        This cubic equation gives us the critical point - the "general area"
        that Trurl refers to before division begins.

        We solve using Newton's method:
        f(x) = x^3 - pnp*x^2 + pnp^2
        f'(x) = 3x^2 - 2*pnp*x

        Returns:
            Approximate x value where constraint equation equals 1
        """
        # Initial guess: x ≈ pnp^(2/3)
        # This comes from the dominant term x^3 ≈ pnp^2 → x ≈ pnp^(2/3)
        # Use string length for log10 approximation to avoid float overflow
        pnp_digits = len(str(self.pnp))
        log_pnp = pnp_digits - 1  # Approximation: log10(number) ≈ digits - 1
        log_x_initial = (2.0 / 3.0) * log_pnp
        x = gmpy2.mpz(10) ** int(log_x_initial)

        # Newton's method: x_new = x - f(x)/f'(x)
        max_iterations = 100
        for iteration in range(max_iterations):
            x_squared = x * x
            x_cubed = x_squared * x

            # f(x) = x^3 - pnp*x^2 + pnp^2
            f_x = x_cubed - self.pnp * x_squared + self.pnp_squared

            # f'(x) = 3x^2 - 2*pnp*x
            f_prime_x = 3 * x_squared - 2 * self.pnp * x

            if f_prime_x == 0:
                break

            # Newton step
            x_new = x - f_x // f_prime_x

            # Check convergence (relative tolerance)
            if abs(x_new - x) < max(1, x // 1000000):
                x = x_new
                break

            x = x_new

        return int(x)

    def find_initial_bounds(self) -> Tuple[int, int]:
        """
        Establish search bounds using Trurl's method with rigorous mathematical analysis.

        Returns:
            (lower_bound, upper_bound) for the smaller factor x

        Mathematical foundation:
        1. Upper bound: x <= sqrt(pnp) always (by definition of smaller factor)

        2. Lower bound requires heuristics based on semiprime type:
           - For RSA-challenge numbers: factors are large and somewhat balanced
           - Trurl's RSA-260 observation: x in [10^90, 10^130]
           - Empirical formula: lower ~ 10^(digits * 0.35)

        3. Derivative critical point: x_c = (pnp^2/2)^(1/3)
           - For x < x_c: function is decreasing (inverse relationship holds)
           - This validates that our search range exhibits the expected behavior

        4. The search range must be in the decreasing region to ensure:
           "If you move x larger y gets smaller" - Trurl
        """
        sqrt_pnp = int(self.sqrt_pnp)
        digits = len(str(self.pnp))

        # === UPPER BOUND ===
        # Always sqrt(pnp) by mathematical necessity (smaller factor <= sqrt)
        upper_bound = sqrt_pnp

        # === LOWER BOUND ===
        # Use Trurl's "find x when y=1" method to get the precise critical point

        # Method 1: Solve for x where constraint equation y = 1
        # This is Trurl's actual first step: "Find x on graph where y on graph equals 1"
        try:
            x_at_y_one = self.find_x_when_y_equals_one()

            # For balanced semiprimes (RSA-class), this gives us the approximate factor location
            # Use this as a starting point, but add safety margin for search
            # Start searching at 70% of this value to account for unbalanced factors
            # Testing shows: 143=11×13 needs ~85%, 1189=29×41 needs ~81%, so 70% is safe
            lower_bound_primary = int(x_at_y_one * 0.7)

            # Verify this is in a reasonable range
            if lower_bound_primary > 2 and lower_bound_primary < sqrt_pnp:
                lower_bound = lower_bound_primary
            else:
                # Fallback to heuristic if y=1 method gives unreasonable value
                raise ValueError("y=1 method out of range")

        except Exception as e:
            # Fallback: Trurl's empirical heuristic for RSA-260 (260 digits → 10^90)
            # 90/260 ≈ 0.346, so we use d * 0.35
            lower_exp_trurl = int(digits * 0.35)
            lower_bound = int(gmpy2.mpz(10) ** lower_exp_trurl)

        # Safety: never go below 2 (smallest prime)
        lower_bound = max(2, int(lower_bound))

        # Safety: never exceed sqrt(pnp)
        lower_bound = min(lower_bound, sqrt_pnp - 1)

        return int(lower_bound), int(upper_bound)

    def verify_factor(self, x: int) -> bool:
        """
        Test if x is a true factor of pnp.

        Args:
            x: Candidate factor

        Returns:
            True if x divides pnp evenly
        """
        return self.pnp % x == 0

    def get_complementary_factor(self, x: int) -> Optional[int]:
        """
        Given one factor, compute the other.

        Args:
            x: Known factor

        Returns:
            The complementary factor y, or None if x doesn't divide pnp
        """
        if self.verify_factor(x):
            return int(self.pnp // x)
        return None

    def verify_all_constraints(self, x: int, y: int) -> Dict[str, bool]:
        """
        Check all of Trurl's constraint equations.

        Args:
            x: Proposed smaller factor
            y: Proposed larger factor

        Returns:
            Dictionary of constraint names and whether they're satisfied
        """
        constraints = {}

        # Constraint 1: pnp = x * y (fundamental)
        constraints['pnp_equals_xy'] = (x * y == self.pnp)

        # Constraint 2: y should match equation output
        computed_y = self.compute_y_from_x(x)
        # Allow small rounding error due to integer division
        constraints['y_equation_match'] = abs(computed_y - y) <= 1

        # Constraint 3: x should be the smaller factor
        constraints['x_is_smaller'] = (x <= y)

        # Constraint 4: Verify inverse relationship holds in neighborhood
        if x > 100:
            # Test x-1 and x+1 if possible
            try:
                y_minus = self.compute_y_from_x(x - 1)
                y_plus = self.compute_y_from_x(x + 1)
                # y should decrease as x increases
                constraints['inverse_relationship'] = (y_minus > y > y_plus)
            except:
                constraints['inverse_relationship'] = None
        else:
            constraints['inverse_relationship'] = None

        return constraints

    def get_search_strategy_params(self, lower: int, upper: int) -> Dict[str, any]:
        """
        Generate search strategy parameters per Trurl's method.

        Args:
            lower: Lower search bound
            upper: Upper search bound

        Returns:
            Dictionary with search parameters
        """
        # Estimate search space size
        range_span = upper - lower

        # Only search primes (massive speedup)
        # Use primesieve to generate primes in [lower, upper]
        # Test each prime p: if pnp % p == 0, found factor

        return {
            'method': 'prime_iteration',
            'lower_bound': int(lower),
            'upper_bound': int(upper),
            'search_space': str(range_span),
            'search_space_digits': len(str(range_span)),
            'strategy': 'iterate primes using primesieve, test divisibility',
            'estimated_primes': range_span // (math.log(upper) if upper > 1 else 1),
        }

    def estimate_progress(self, current: int, lower: int, upper: int) -> float:
        """
        Estimate search progress on logarithmic scale.

        Since the search space is exponentially large, linear progress
        would be misleading. Use log scale.

        Args:
            current: Current test value
            lower: Lower bound
            upper: Upper bound

        Returns:
            Progress percentage (0-100)
        """
        if upper <= lower or current < lower:
            return 0.0
        if current >= upper:
            return 100.0

        try:
            log_current = math.log10(max(1, current))
            log_lower = math.log10(max(1, lower))
            log_upper = math.log10(max(1, upper))

            if log_upper <= log_lower:
                return 100.0

            progress = ((log_current - log_lower) / (log_upper - log_lower)) * 100.0
            return min(100.0, max(0.0, progress))
        except (ValueError, ZeroDivisionError):
            return 0.0

    def diagnostic_report(self, x_test: Optional[int] = None) -> Dict[str, any]:
        """
        Generate comprehensive diagnostic information about the equation behavior.

        Args:
            x_test: Optional test value to evaluate

        Returns:
            Diagnostic data with mathematical analysis
        """
        import math

        report = {
            'pnp': str(self.pnp),
            'pnp_digits': len(str(self.pnp)),
            'sqrt_pnp': str(self.sqrt_pnp),
            'sqrt_pnp_digits': len(str(self.sqrt_pnp)),
        }

        # Compute initial bounds with detailed rationale
        lower, upper = self.find_initial_bounds()
        report['computed_lower_bound'] = str(lower)
        report['computed_upper_bound'] = str(upper)
        # Use string length for log approximation to avoid overflow
        report['lower_bound_exponent'] = len(str(lower)) - 1 if lower > 0 else 0
        report['upper_bound_exponent'] = len(str(upper)) - 1 if upper > 0 else 0

        # Calculate the Trurl coefficient: for RSA-260, 90/260 ≈ 0.346
        if len(str(self.pnp)) > 0:
            trurl_coefficient = report['lower_bound_exponent'] / len(str(self.pnp))
            report['trurl_coefficient'] = trurl_coefficient
            report['trurl_match_rsa260'] = abs(trurl_coefficient - 0.346) < 0.01

        # Compute Trurl's x where y=1 (the "general area" before division)
        try:
            x_at_y_one = self.find_x_when_y_equals_one()
            y_verify = self.compute_constraint_value(x_at_y_one)
            # Use string length for log approximation to avoid overflow
            x_exp = len(str(x_at_y_one)) - 1 if x_at_y_one > 0 else 0

            report['x_when_y_equals_one'] = str(x_at_y_one)
            report['x_when_y_equals_one_exponent'] = x_exp
            report['x_when_y_equals_one_digits'] = len(str(x_at_y_one))
            report['y_value_at_x'] = y_verify
            report['y_close_to_one'] = abs(y_verify - 1.0) < 0.01
        except Exception as e:
            report['x_when_y_equals_one'] = f'calculation_failed: {str(e)}'

        # Compute critical point where derivative changes sign
        try:
            critical_point = self.find_critical_point_derivative()
            # Use string length for log approximation to avoid overflow
            critical_exp = len(str(critical_point)) - 1 if critical_point > 0 else 0
            report['critical_point'] = str(critical_point)
            report['critical_point_exponent'] = critical_exp
            report['upper_bound_below_critical'] = upper < critical_point
            report['entire_range_in_decreasing_region'] = upper < critical_point
        except:
            report['critical_point'] = 'calculation_failed'

        # Verify decreasing region for bounds
        report['lower_in_decreasing_region'] = self.verify_decreasing_region(lower)
        report['upper_in_decreasing_region'] = self.verify_decreasing_region(upper)

        # If test value provided, evaluate it
        if x_test:
            y_test = self.compute_y_from_x(x_test)
            constraint = self.compute_constraint_value(x_test)

            report['test_x'] = str(x_test)
            report['computed_y'] = str(y_test)
            report['constraint_value'] = constraint
            report['is_factor'] = self.verify_factor(x_test)
            report['in_decreasing_region'] = self.verify_decreasing_region(x_test)

            if self.verify_factor(x_test):
                true_y = self.get_complementary_factor(x_test)
                constraints = self.verify_all_constraints(x_test, true_y)

                # Theoretical analysis
                error = y_test - true_y
                # Avoid float overflow for large numbers
                try:
                    theoretical_error = float(x_test) / float(true_y) if true_y > 0 else 0
                except OverflowError:
                    theoretical_error = "overflow - numbers too large"

                report['true_y'] = str(true_y)
                report['all_constraints'] = constraints
                report['equation_error'] = int(error)
                report['theoretical_error'] = theoretical_error
                report['error_analysis'] = {
                    'actual_error': int(error),
                    'expected_error_x_over_y': theoretical_error,
                    'error_is_small': abs(error) <= 1,
                    'explanation': 'y_computed = y_true + x/y_true (from mathematical derivation)'
                }

        return report
