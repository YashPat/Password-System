"""
Configuration module for password generation and recovery system.
Handles computation parameters, calibration, and time estimation.
"""
import hashlib
import time
from typing import Tuple

# Target computation time in seconds (15 hours)
TARGET_COMPUTATION_TIME = 15 * 60 * 60  # 54000 seconds

# Number of test iterations for calibration
CALIBRATION_TEST_ITERATIONS = 20000000

def calibrate_iterations(target_time: float = TARGET_COMPUTATION_TIME) -> int:
    """
    Calibrate the number of iterations needed to achieve target computation time.
    
    Args:
        target_time: Target time in seconds (default: 15 hours)
    
    Returns:
        Estimated number of iterations needed for target time
    """
    print(f"Calibrating computation speed (running {CALIBRATION_TEST_ITERATIONS} test iterations)...")
    
    # Test data
    test_seed = b"calibration_test"
    test_hash = test_seed
    
    # Time the test iterations
    start_time = time.time()
    for _ in range(CALIBRATION_TEST_ITERATIONS):
        test_hash = hashlib.sha256(test_hash).digest()
    elapsed_time = time.time() - start_time
    
    # Calculate iterations per second
    iterations_per_second = CALIBRATION_TEST_ITERATIONS / elapsed_time
    
    # Calculate total iterations needed
    total_iterations = int(iterations_per_second * target_time)
    
    print(f"Calibration complete:")
    print(f"  Speed: {iterations_per_second:.2f} iterations/second")
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
    # Run a quick calibration if needed
    test_iterations = min(10000, iterations // 100)
    if test_iterations < 100:
        test_iterations = 100
    
    test_seed = b"time_estimation"
    test_hash = test_seed
    
    start_time = time.time()
    for _ in range(test_iterations):
        test_hash = hashlib.sha256(test_hash).digest()
    elapsed_time = time.time() - start_time
    
    iterations_per_second = test_iterations / elapsed_time
    estimated_time = iterations / iterations_per_second
    
    return estimated_time
