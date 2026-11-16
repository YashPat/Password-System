"""
Password generator module for password generation.
Generates a random seed and computes password using proof-of-work.
"""
import secrets
from typing import Optional, Tuple
import config
from password_recovery import ProgressCallback, hash_to_password, _perform_iterative_hashing


def generate_random_seed() -> str:
    """
    Generate a random seed value.
    
    Returns:
        Random hexadecimal seed string
    """
    # Generate 32 random bytes (256 bits)
    random_bytes = secrets.token_bytes(32)
    return random_bytes.hex()


def create_password_with_keys(
    on_progress: Optional[ProgressCallback] = None, verbose: bool = True
) -> Tuple[str, str, int]:
    """
    Create a new password and generate recovery keys.
    
    This function generates a random seed and computes a password using
    expensive iterative hashing (proof-of-work). The same computation is
    required for password recovery, ensuring security.
    
    Args:
        on_progress: Optional progress callback (see _perform_iterative_hashing);
            when given, nothing is printed during hashing
        verbose: Whether calibration prints its results (default: True)
    
    Returns:
        Tuple of (password, seed, iterations)
    """
    # Generate random seed
    seed = generate_random_seed()
    
    # Calibrate iterations for target time (15 hours)
    iterations = config.calibrate_iterations(verbose=verbose)
    
    # Compute password using the same proof-of-work as recovery
    # This ensures the password cannot be derived without doing the work
    seed_bytes = bytes.fromhex(seed)
    final_hash = _perform_iterative_hashing(
        seed_bytes, iterations, show_progress=True, on_progress=on_progress
    )
    password = hash_to_password(final_hash)
    
    return password, seed, iterations
