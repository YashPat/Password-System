"""
Core SHA-256 hash chain shared by password computation and speed calibration.

Calibration and the real computation both call hash_chain, so the measured
speed matches the speed of the work that actually runs.
"""
import hashlib


def hash_chain(current_hash: bytes, count: int) -> bytes:
    """
    Apply SHA-256 to current_hash `count` times in a row.

    Args:
        current_hash: Starting bytes
        count: Number of SHA-256 applications

    Returns:
        Hash bytes after `count` applications
    """
    sha256 = hashlib.sha256
    for _ in range(count):
        current_hash = sha256(current_hash).digest()
    return current_hash
