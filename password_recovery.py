"""
Password recovery module for expensive password computation.
Uses iterative hashing to regenerate password from recovery keys.
"""
import hashlib
from typing import Optional
import config

# Password length constant (local to this module)
_PASSWORD_LENGTH = 15


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


def _perform_iterative_hashing(seed_bytes: bytes, iterations: int, show_progress: bool = True) -> bytes:
    """
    Perform iterative SHA-256 hashing on seed bytes.
    
    This is the core proof-of-work computation. Starting from the hashed seed,
    it performs the specified number of SHA-256 iterations. The final hash
    is used to derive the password, ensuring that password recovery requires
    the full computational work.
    
    Args:
        seed_bytes: The seed as bytes
        iterations: Number of hash iterations to perform
        show_progress: Whether to show progress percentage (default: True)
    
    Returns:
        Final hash bytes after all iterations
    """
    # Start from the hashed seed
    current_hash = hashlib.sha256(seed_bytes).digest()
    
    if show_progress:
        # Lightweight progress display: update on increments
        # ANSI color code: \033[92m = bright green, \033[0m = reset
        print("\033[92mComputing password:\033[0m ", end="", flush=True)
        
        for i in range(iterations):
            current_hash = hashlib.sha256(current_hash).digest()
            
            progress_increment = 5000000
            # Update progress every X iteration for performance reasons
            if (i + 1) % progress_increment == 0 or (i + 1) == iterations:
                percentage = ((i + 1) / iterations) * 100
                print(f"\r\033[92mComputing password:\033[0m {percentage:0.3f}%", end="", flush=True)
        
        print()  # New line after completion
    else:
        # No progress display, just do the iterations
        for _ in range(iterations):
            current_hash = hashlib.sha256(current_hash).digest()
    
    return current_hash


def recover_password(seed: str, iterations: int) -> Optional[str]:
    """
    Recover password from seed using expensive iterative hashing.
    
    This function performs expensive computation (proof of work) that requires
    the full number of iterations. The password is derived from the final
    iterated hash, ensuring that password recovery cannot be bypassed.
    
    Args:
        seed: The seed value from recovery keys
        iterations: Number of iterations to perform (proof of work)
    
    Returns:
        Recovered password, or None if error occurs
    """
    try:
        # Convert seed hex string to bytes
        seed_bytes = bytes.fromhex(seed)
        
        # Perform expensive iterative hashing (proof of work)
        # This takes ~15 hours but ensures the password can only be
        # recovered by doing the expensive computation
        final_hash = _perform_iterative_hashing(seed_bytes, iterations, show_progress=True)
        
        # Derive password from the final iterated hash
        # This ensures the password requires proof-of-work to recover
        password = hash_to_password(final_hash)
        
        return password
        
    except Exception as e:
        print(f"Error during password recovery: {e}")
        return None
