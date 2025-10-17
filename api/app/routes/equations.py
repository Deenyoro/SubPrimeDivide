"""
Equation visualization and analysis endpoints.

Provides API for plotting Trurl equation curves and analyzing bounds.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import math
from decimal import Decimal, getcontext
import hashlib
from datetime import datetime

from ..models.database import get_db, EquationSnapshot
from ..equations.semiprime_equation import SemiPrimeEquationSolver

router = APIRouter(prefix="/equations", tags=["equations"])

# Set high precision for equation calculations
getcontext().prec = 150


@router.get("/curve")
async def get_equation_curve(
    n: str = Query(..., description="Semiprime number to analyze"),
    x_min: Optional[str] = Query(None, description="Minimum x value for curve"),
    x_max: Optional[str] = Query(None, description="Maximum x value for curve"),
    points: int = Query(500, ge=10, le=2000, description="Number of points to compute"),
    db: Session = Depends(get_db)
):
    """
    Compute equation curve points for visualization.

    Returns x/y coordinates for the Trurl equation:
    y = (((N²/x) + x²) / N)

    Also includes bounds and constraint information.
    """
    try:
        # Parse the semiprime
        pnp = int(n)
        if pnp < 2:
            raise HTTPException(status_code=400, detail="Number must be >= 2")

        # Initialize solver
        solver = SemiPrimeEquationSolver(pnp)

        # Get bounds if not provided
        if x_min is None or x_max is None:
            lower, upper = solver.find_initial_bounds()
            if x_min is None:
                x_min = str(lower)
            if x_max is None:
                # Use upper bound but cap for visualization
                x_max = str(min(upper, lower * 1000))  # Show reasonable range

        x_min_val = int(x_min)
        x_max_val = int(x_max)

        # Validate range
        if x_min_val >= x_max_val:
            raise HTTPException(status_code=400, detail="x_min must be < x_max")

        # Compute curve points (logarithmic spacing for better visualization)
        curve_points = []

        # Use logarithmic spacing for better visualization of exponential behavior
        log_min = math.log10(x_min_val) if x_min_val > 0 else 0
        log_max = math.log10(x_max_val)
        step = (log_max - log_min) / (points - 1)

        for i in range(points):
            log_x = log_min + i * step
            x = int(10 ** log_x)

            # Clamp to valid range
            if x < x_min_val:
                x = x_min_val
            if x > x_max_val:
                x = x_max_val

            try:
                y = solver.compute_y_from_x(x)
                constraint = solver.compute_constraint_value(x)
                is_factor = solver.verify_factor(x)

                curve_points.append({
                    "x": str(x),
                    "y": str(y),
                    "constraint": float(constraint),
                    "is_candidate": abs(constraint - 2.0) < 0.1,  # Close to ideal constraint
                    "is_factor": is_factor
                })
            except Exception as e:
                # Skip points that cause calculation errors
                continue

        # Get bounds information
        lower_bound, upper_bound = solver.find_initial_bounds()

        # Compute x where y=1 (Trurl's critical point)
        try:
            crossover = solver.find_x_when_y_equals_one()
        except:
            crossover = None

        # Get diagnostic information
        diagnostic = solver.diagnostic_report()

        response = {
            "n": n,
            "x_min": x_min,
            "x_max": x_max,
            "points_requested": points,
            "points_computed": len(curve_points),
            "curve_points": curve_points,
            "bounds": {
                "lower": str(lower_bound),
                "upper": str(upper_bound),
                "crossover": str(crossover) if crossover else None
            },
            "diagnostic": {
                "digits": len(str(pnp)),
                "sqrt_n": str(int(math.sqrt(pnp))),
                "equation": "y = (((N²/x) + x²) / N)",
                "constraint_ideal": 2.0,
                **diagnostic
            }
        }

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid number format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing curve: {str(e)}")


@router.post("/snapshot")
async def save_equation_snapshot(
    job_id: str,
    x_min: str,
    x_max: str,
    step: int,
    points_blob: List[dict],
    db: Session = Depends(get_db)
):
    """
    Save an equation visualization snapshot for later retrieval.

    Useful for caching expensive computations and sharing visualizations.
    """
    try:
        snapshot = EquationSnapshot(
            job_id=job_id,
            x_min=x_min,
            x_max=x_max,
            step=step,
            points_blob=points_blob,
            created_at=datetime.utcnow()
        )

        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)

        return {
            "id": snapshot.id,
            "job_id": snapshot.job_id,
            "created_at": snapshot.created_at.isoformat(),
            "points_count": len(points_blob)
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving snapshot: {str(e)}")


@router.get("/snapshots/{job_id}")
async def get_equation_snapshots(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve all equation snapshots for a job.
    """
    snapshots = db.query(EquationSnapshot).filter(
        EquationSnapshot.job_id == job_id
    ).order_by(EquationSnapshot.created_at.desc()).all()

    return {
        "job_id": job_id,
        "snapshots": [
            {
                "id": s.id,
                "x_min": s.x_min,
                "x_max": s.x_max,
                "step": s.step,
                "points_count": len(s.points_blob) if s.points_blob else 0,
                "created_at": s.created_at.isoformat()
            }
            for s in snapshots
        ]
    }


@router.get("/snapshots/{job_id}/{snapshot_id}")
async def get_equation_snapshot_detail(
    job_id: str,
    snapshot_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific equation snapshot with full data.
    """
    snapshot = db.query(EquationSnapshot).filter(
        EquationSnapshot.id == snapshot_id,
        EquationSnapshot.job_id == job_id
    ).first()

    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    return {
        "id": snapshot.id,
        "job_id": snapshot.job_id,
        "x_min": snapshot.x_min,
        "x_max": snapshot.x_max,
        "step": snapshot.step,
        "points_blob": snapshot.points_blob,
        "created_at": snapshot.created_at.isoformat()
    }


@router.get("/analyze/{n}")
async def analyze_semiprime_equation(
    n: str,
    test_x: Optional[str] = None
):
    """
    Get detailed analysis of semiprime using equation method.

    Provides bounds, constraint analysis, and diagnostic information.
    """
    try:
        pnp = int(n)
        solver = SemiPrimeEquationSolver(pnp)

        # Get bounds
        lower, upper = solver.find_initial_bounds()

        # Get x where y=1 (critical point)
        try:
            crossover = solver.find_x_when_y_equals_one()
        except:
            crossover = None

        # Get search strategy
        strategy = solver.get_search_strategy_params(lower, upper)

        # Get diagnostic report
        test_x_val = int(test_x) if test_x else None
        diagnostic = solver.diagnostic_report(x_test=test_x_val)

        return {
            "n": n,
            "digits": len(str(pnp)),
            "bounds": {
                "lower": str(lower),
                "upper": str(upper),
                "crossover": str(crossover) if crossover else None
            },
            "strategy": strategy,
            "diagnostic": diagnostic,
            "recommendations": {
                "use_equation_guided": len(str(pnp)) > 20,
                "estimated_primes_to_test": strategy.get("estimated_primes"),
                "suggested_algorithms": get_suggested_algorithms(pnp)
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid number format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing semiprime: {str(e)}")


def get_suggested_algorithms(n: int) -> List[str]:
    """
    Suggest algorithms based on number size.
    """
    digits = len(str(n))

    suggestions = []

    if digits < 20:
        suggestions.extend(["trial_division", "pollard_rho"])
    elif digits < 40:
        suggestions.extend(["pollard_rho", "ecm"])
    elif digits < 60:
        suggestions.extend(["ecm", "equation_guided"])
    elif digits < 90:
        suggestions.extend(["ecm", "equation_guided", "quadratic_sieve"])
    else:
        suggestions.extend(["ecm", "gnfs"])

    return suggestions


@router.get("/find-x-when-y-one/{n}")
async def find_x_when_y_one(n: str):
    """
    Find x where Trurl's constraint equation y=1.

    This is Trurl's first step: "Find x on graph where y on graph equals 1"

    The equation: y = ((((pnp^2 / x) + x^2) / x) / pnp) = 1

    Returns the "general area" before division/prime searching begins.

    Example: GET /api/equations/find-x-when-y-one/143
    Returns x ≈ 13 (actual factors are 11 and 13)
    """
    try:
        pnp = int(n)
        if pnp < 2:
            raise HTTPException(status_code=400, detail="Number must be >= 2")

        solver = SemiPrimeEquationSolver(pnp)

        # Find x where y=1
        x = solver.find_x_when_y_equals_one()

        # Verify by computing y at this x
        y = solver.compute_constraint_value(x)

        x_exp = math.log10(x) if x > 0 else 0

        return {
            "success": True,
            "n": n,
            "n_digits": len(str(pnp)),
            "x_when_y_equals_one": str(x),
            "x_digits": len(str(x)),
            "x_exponent": x_exp,
            "y_value_at_x": y,
            "y_close_to_one": abs(y - 1.0) < 0.01,
            "equation": "y = ((((N²/x) + x²) / x) / N)",
            "explanation": "This x value represents the 'general area' where the smaller factor is located"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid number format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")


@router.get("/compute-constraint/{n}/{x}")
async def compute_constraint(n: str, x: str):
    """
    Compute Trurl's constraint equation for given pnp and x.

    y = ((((pnp^2 / x) + x^2) / x) / pnp)

    Example: GET /api/equations/compute-constraint/143/11
    Returns y ≈ 1.259 (since 11 is a factor of 143)
    """
    try:
        pnp = int(n)
        x_val = int(x)

        if pnp < 2:
            raise HTTPException(status_code=400, detail="Number must be >= 2")
        if x_val < 1:
            raise HTTPException(status_code=400, detail="x must be >= 1")

        solver = SemiPrimeEquationSolver(pnp)
        y = solver.compute_constraint_value(x_val)

        # Check if x is actually a factor
        is_factor = solver.verify_factor(x_val)

        return {
            "success": True,
            "n": n,
            "x": x,
            "y": y,
            "is_factor": is_factor,
            "equation": "y = ((((N²/x) + x²) / x) / N)",
            "interpretation": {
                "y_near_one": abs(y - 1.0) < 0.1,
                "likely_close_to_factor": abs(y - 1.0) < 0.1,
                "is_actual_factor": is_factor
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid number format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")
