"""
CADO-NFS (General Number Field Sieve) wrapper for large semiprime factorization.

CADO-NFS is the industry-standard GNFS implementation for factoring 200+ digit composites.
This wrapper interfaces with the cado-nfs.py script and provides progress monitoring.
"""

import subprocess
import os
import shutil
import re
import time
import tempfile
from pathlib import Path
from typing import Optional, Tuple, Callable

# Check if cado-nfs.py is available
HAS_CADO = shutil.which("cado-nfs.py") is not None


def cado_nfs_factor(
    n: int,
    workdir: Optional[str] = None,
    threads: int = 4,
    expected_factor_digits: Optional[int] = None,
    callback: Optional[Callable[[str], None]] = None,
    timeout: Optional[int] = None
) -> Optional[Tuple[int, int]]:
    """
    Factor a large semiprime using CADO-NFS.

    Args:
        n: The semiprime to factor
        workdir: Working directory for CADO-NFS (auto-created if None)
        threads: Number of threads to use
        expected_factor_digits: Hint for polynomial selection (from Trurl bounds)
        callback: Optional callback function(log_line) for progress updates
        timeout: Maximum runtime in seconds (None = unlimited)

    Returns:
        Tuple of (p, q) if factorization succeeds, None otherwise

    Note:
        CADO-NFS is designed for multi-week/month runs on 200+ digit semiprimes.
        For RSA-260, expect weeks to months even on multi-core systems.
    """
    if not HAS_CADO:
        if callback:
            callback("CADO-NFS not available. Install cado-nfs package.")
        return None

    # Create working directory
    cleanup_workdir = False
    if workdir is None:
        workdir = tempfile.mkdtemp(prefix=f"cado_nfs_{n % 1000000}_")
        cleanup_workdir = True

    workdir_path = Path(workdir)
    workdir_path.mkdir(parents=True, exist_ok=True)

    # Write number to input file
    input_file = workdir_path / "input.txt"
    input_file.write_text(str(n))

    try:
        # Build CADO-NFS command
        cmd = [
            "cado-nfs.py",
            str(n),
            f"--workdir={workdir}",
            f"--threads={threads}",
        ]

        # Add polynomial selection hints if we have expected factor size
        if expected_factor_digits:
            # Inform CADO that we expect a factor around 10^expected_factor_digits
            # This helps polynomial selection target the right scale
            cmd.append(f"--polysel-admax={10**expected_factor_digits}")
            if callback:
                callback(f"CADO-NFS: Using Trurl hint - expected factor ~10^{expected_factor_digits} digits")

        if callback:
            callback(f"CADO-NFS: Starting factorization of {len(str(n))}-digit semiprime")
            callback(f"CADO-NFS: Command: {' '.join(cmd)}")
            callback(f"CADO-NFS: Workdir: {workdir}")
            callback(f"CADO-NFS: Note - This may take weeks to months for RSA-260 scale")

        # Run CADO-NFS with real-time log streaming
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
            cwd=workdir
        )

        start_time = time.time()
        factors = []

        # Stream output and look for factors
        for line in iter(process.stdout.readline, ''):
            if not line:
                break

            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                process.terminate()
                if callback:
                    callback(f"CADO-NFS: Timeout after {timeout}s")
                break

            # Send progress to callback
            if callback:
                callback(f"CADO-NFS: {line.rstrip()}")

            # Parse for factors in CADO-NFS output
            # CADO outputs: "Factors found: p q" or similar
            factor_match = re.search(r'(?:Factors?|prp\d+):\s*(\d+)(?:\s+(\d+))?', line, re.IGNORECASE)
            if factor_match:
                p = int(factor_match.group(1))
                q = int(factor_match.group(2)) if factor_match.group(2) else None

                if p and q and p * q == n:
                    factors = [p, q]
                    if callback:
                        callback(f"CADO-NFS: ✓ Factorization complete!")
                        callback(f"CADO-NFS: Found factors: {p} × {q}")
                    break
                elif p and n % p == 0:
                    q = n // p
                    factors = [p, q]
                    if callback:
                        callback(f"CADO-NFS: ✓ Factorization complete!")
                        callback(f"CADO-NFS: Found factors: {p} × {q}")
                    break

        # Wait for process to complete
        process.wait()

        if factors and len(factors) == 2:
            return tuple(sorted(factors))

        # Check output files for factors
        # CADO-NFS writes factors to <workdir>/<n>.factors.txt
        factors_file = workdir_path / f"{n}.factors.txt"
        if factors_file.exists():
            content = factors_file.read_text().strip()
            numbers = re.findall(r'\d+', content)
            if len(numbers) >= 2:
                p, q = int(numbers[0]), int(numbers[1])
                if p * q == n:
                    if callback:
                        callback(f"CADO-NFS: Found factors in output file: {p} × {q}")
                    return tuple(sorted([p, q]))

        if callback:
            callback("CADO-NFS: Factorization incomplete (no factors found)")

        return None

    except subprocess.TimeoutExpired:
        if callback:
            callback(f"CADO-NFS: Process timeout after {timeout}s")
        return None

    except Exception as e:
        if callback:
            callback(f"CADO-NFS error: {e}")
        return None

    finally:
        # Cleanup temporary workdir if created
        if cleanup_workdir and workdir_path.exists():
            try:
                shutil.rmtree(workdir)
            except:
                pass  # Best effort cleanup


def estimate_cado_runtime(digit_count: int) -> dict:
    """
    Estimate CADO-NFS runtime based on semiprime size.

    Based on community timings for GNFS:
    - 150 digits: days
    - 200 digits: weeks
    - 232 digits (RSA-768): ~2 years with 2000 CPU cores
    - 260 digits (RSA-260): months to years with significant resources

    Returns:
        Dictionary with runtime estimate and resource recommendations
    """
    if digit_count < 100:
        return {
            'method': 'Use ECM instead',
            'estimated_time': 'N/A (CADO overkill for <100 digits)',
            'cpu_cores': 1,
            'memory_gb': 1
        }
    elif digit_count < 150:
        return {
            'method': 'GNFS (CADO-NFS)',
            'estimated_time': 'Hours to days',
            'cpu_cores': 4-8,
            'memory_gb': 4-8
        }
    elif digit_count < 200:
        return {
            'method': 'GNFS (CADO-NFS)',
            'estimated_time': 'Days to weeks',
            'cpu_cores': 16-32,
            'memory_gb': 16-32
        }
    elif digit_count < 250:
        return {
            'method': 'GNFS (CADO-NFS) + distributed cluster',
            'estimated_time': 'Weeks to months',
            'cpu_cores': '100+ (cluster)',
            'memory_gb': '64-128 per node',
            'notes': 'RSA-768 (232 digits) took ~2 years with 2000 cores (2009)'
        }
    else:
        return {
            'method': 'GNFS (CADO-NFS) + massive distributed cluster',
            'estimated_time': 'Months to years',
            'cpu_cores': '1000+ (large cluster)',
            'memory_gb': '128-256 per node',
            'notes': 'RSA-260 unfactored as of 2025. Requires world-class resources.'
        }
