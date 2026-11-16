"""
Configuration module for password generation and recovery system.
Handles computation parameters, calibration, and time estimation.
"""
import time

from hashing import hash_chain

# Target computation time in seconds (15 hours)
TARGET_COMPUTATION_TIME = 15 * 60 * 60  # 54000 seconds

# How long to measure hashing speed for. A very short measurement catches the
# CPU before it has ramped up and makes the computation look slower than it is.
CALIBRATION_SECONDS = 2.0

# Untimed hashing before measuring, so the CPU is already at full speed
WARMUP_ITERATIONS = 2_000_000

# Hashes per timed chunk while measuring
_MEASURE_CHUNK = 1_000_000


def measure_speed(min_seconds: float = CALIBRATION_SECONDS) -> float:
    """
    Measure hashing speed with the same loop the real computation uses.

    Args:
        min_seconds: Minimum time to spend measuring

    Returns:
        Iterations per second
    """
    test_hash = hash_chain(b"calibration_test", WARMUP_ITERATIONS)

    done = 0
    start_time = time.perf_counter()
    while True:
        test_hash = hash_chain(test_hash, _MEASURE_CHUNK)
        done += _MEASURE_CHUNK
        elapsed_time = time.perf_counter() - start_time
        if elapsed_time >= min_seconds:
            return done / elapsed_time


def calibrate_iterations(target_time: float = TARGET_COMPUTATION_TIME) -> int:
    """
    Calibrate the number of iterations needed to achieve target computation time.

    Args:
        target_time: Target time in seconds (default: 15 hours)

    Returns:
        Estimated number of iterations needed for target time
    """
    print(f"Calibrating computation speed (about {CALIBRATION_SECONDS:.0f} seconds)...")

    iterations_per_second = measure_speed()

    # Calculate total iterations needed
    total_iterations = int(iterations_per_second * target_time)

    print(f"Calibration complete:")
    print(f"  Speed: {iterations_per_second:,.0f} iterations/second")
    print(f"  Estimated iterations for {target_time/3600:.1f} hours: {total_iterations:,}")

    return total_iterations


def estimate_time(iterations: int) -> float:
    """
    Estimate computation time based on iteration count.

    Args:
        iterations: Number of iterations

    Returns:
        Estimated time in seconds
    """
    return iterations / measure_speed()


def format_duration(seconds: float) -> str:
    """
    Format a duration as a short human-readable string, e.g. "8h 12m".

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration
    """
    total_minutes = int(seconds // 60)
    hours, minutes = divmod(total_minutes, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m"
    return f"{int(seconds)}s"
