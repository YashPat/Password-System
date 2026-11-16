"""
Utility functions for validation, key formatting, and helper operations.
"""
import json
import re
from typing import Dict, Optional


def validate_password_length(password: str, max_length: int = 15) -> bool:
    """Validate that password doesn't exceed maximum length."""
    return len(password) <= max_length


def validate_alphanumeric(password: str) -> bool:
    """Validate that password contains only alphanumeric characters."""
    return bool(re.match(r'^[a-zA-Z0-9]+$', password))


def format_keys(seed: str, iterations: int) -> str:
    """
    Format recovery keys as a JSON string.
    
    Args:
        seed: The seed value used for password generation
        iterations: Number of iterations for recovery computation
    
    Returns:
        JSON-formatted string with keys
    """
    keys = {
        "seed": seed,
        "iterations": iterations
    }
    return json.dumps(keys, indent=2)


def parse_keys(keys_string: str) -> Optional[Dict]:
    """
    Parse recovery keys from JSON string.
    
    Args:
        keys_string: JSON-formatted string with keys
    
    Returns:
        Dictionary with seed and iterations, or None if parsing fails
    """
    try:
        keys = json.loads(keys_string)
        if not isinstance(keys, dict):
            return None
        if "seed" not in keys or "iterations" not in keys:
            return None
        return keys
    except json.JSONDecodeError:
        return None


def validate_keys(keys: Dict) -> bool:
    """
    Validate that keys dictionary has required fields.
    
    Args:
        keys: Dictionary with keys
    
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(keys, dict):
        return False
    if "seed" not in keys or "iterations" not in keys:
        return False
    if not isinstance(keys["seed"], str) or not isinstance(keys["iterations"], int):
        return False
    if keys["iterations"] <= 0:
        return False
    return True
