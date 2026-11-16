"""
Password recovery module for expensive password computation.
Uses iterative hashing to regenerate password from recovery keys.
"""
import hashlib
import time
from typing import Callable, Optional
import config
from hashing import hash_chain

# Password length constant (local to this module)
_PASSWORD_LENGTH = 15

# Iterations between progress updates
_PROGRESS_INCREMENT = 5_000_000

_PROGRESS_LABEL = "\033[92mComputing password:\033[0m"

# Called as on_progress(done, total, elapsed_seconds) after each chunk.
# Raising ComputationCancelled from it stops the computation.
ProgressCallback = Callable[[int, int, float], None]


class ComputationCancelled(Exception):
    """Raised by a progress callback to stop a computation early."""


def hash_to_password(hash_bytes: bytes) -> str:
    """
    Convert hash bytes to hex password.
    
    Args:
        hash_bytes: Hash bytes to convert
    
    Returns:
        Hex password string (15 characters, 0-9, a-f)
    """
    hash_hex = hash_bytes.hex()
    return hash_hex[:_PASSWORD_LENGTH]


def _perform_iterative_hashing(
    seed_bytes: bytes,
    iterations: int,
    show_progress: bool = True,
    on_progress: Optional[ProgressCallback] = None,
) -> bytes:
    """
    Perform iterative SHA-256 hashing on seed bytes.
    
    This is the core proof-of-work computation. Starting from the hashed seed,
    it performs the specified number of SHA-256 iterations. The final hash
    is used to derive the password, ensuring that password recovery requires
    the full computational work.
    
    Args:
        seed_bytes: The seed as bytes
        iterations: Number of hash iterations to perform
        show_progress: Whether to print a progress line (default: True);
            ignored when on_progress is given
        on_progress: Optional callback receiving (done, total, elapsed_seconds)
            after each chunk; nothing is printed when it is given
    
    Returns:
        Final hash bytes after all iterations
    """
    # Start from the hashed seed
    current_hash = hashlib.sha256(seed_bytes).digest()

    if on_progress is not None:
        return _hash_in_chunks(current_hash, iterations, on_progress)
    if not show_progress:
        return hash_chain(current_hash, iterations)

    print(f"{_PROGRESS_LABEL} 0.000%", end="", flush=True)
    current_hash = _hash_in_chunks(current_hash, iterations, _print_progress)
    print()  # New line after completion
    return current_hash


def _hash_in_chunks(current_hash: bytes, iterations: int, on_progress: ProgressCallback) -> bytes:
    """
    Run the hash chain in chunks, reporting progress after each chunk.

    Reporting only between chunks keeps the cost of progress updates
    negligible next to the hashing itself.
    """
    done = 0
    start_time = time.perf_counter()
    while done < iterations:
        chunk = min(_PROGRESS_INCREMENT, iterations - done)
        current_hash = hash_chain(current_hash, chunk)
        done += chunk
        on_progress(done, iterations, time.perf_counter() - start_time)
    return current_hash


def _print_progress(done: int, total: int, elapsed: float) -> None:
    """Progress callback for the plain CLI: one updating terminal line."""
    # The time remaining comes from the speed actually achieved so far,
    # so it stays accurate if the machine speeds up or slows down.
    percentage = (done / total) * 100
    status = f"{percentage:0.3f}%"
    if done < total:
        remaining = elapsed * (total - done) / done
        status += f"  ~{config.format_duration(remaining)} left"
    # Trailing spaces clear any longer text left from the previous update
    print(f"\r{_PROGRESS_LABEL} {status}    ", end="", flush=True)


def recover_password(
    seed: str, iterations: int, on_progress: Optional[ProgressCallback] = None
) -> Optional[str]:
    """
    Recover password from seed using expensive iterative hashing.
    
    This function performs expensive computation (proof of work) that requires
    the full number of iterations. The password is derived from the final
    iterated hash, ensuring that password recovery cannot be bypassed.
    
    Args:
        seed: The seed value from recovery keys
        iterations: Number of iterations to perform (proof of work)
        on_progress: Optional progress callback (see _perform_iterative_hashing)
    
    Returns:
        Recovered password, or None if error occurs
    
    Raises:
        ComputationCancelled: If on_progress cancels the computation
    """
    try:
        # Convert seed hex string to bytes
        seed_bytes = bytes.fromhex(seed)
        
        # Perform expensive iterative hashing (proof of work)
        # This takes ~15 hours but ensures the password can only be
        # recovered by doing the expensive computation
        final_hash = _perform_iterative_hashing(
            seed_bytes, iterations, show_progress=True, on_progress=on_progress
        )
        
        # Derive password from the final iterated hash
        # This ensures the password requires proof-of-work to recover
        password = hash_to_password(final_hash)
        
        return password
        
    except ComputationCancelled:
        raise
    except Exception as e:
        print(f"Error during password recovery: {e}")
        return None
