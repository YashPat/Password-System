"""
Regression test: fixed recovery keys must always produce the same passwords.

Existing recovery keys depend on the exact hashing, so any change that alters
these outputs would make previously saved keys recover the wrong password.

Run with: python3 -m unittest test_passwords
"""
import contextlib
import io
import unittest

from password_recovery import _perform_iterative_hashing, hash_to_password, recover_password

# (seed, iterations, expected password), recorded from the original implementation
KNOWN_KEYS = [
    ("00" * 32, 1, "2b32db6c2c0a623"),
    ("ab" * 32, 1000, "f8442cf378e8c06"),
    ("0123456789abcdef" * 4, 5_000_000, "b523b43dd951b03"),
]


class KnownKeysTest(unittest.TestCase):
    def test_recovery_with_progress(self):
        for seed, iterations, expected in KNOWN_KEYS:
            with self.subTest(iterations=iterations):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(recover_password(seed, iterations), expected)

    def test_hashing_without_progress(self):
        for seed, iterations, expected in KNOWN_KEYS:
            with self.subTest(iterations=iterations):
                final_hash = _perform_iterative_hashing(
                    bytes.fromhex(seed), iterations, show_progress=False
                )
                self.assertEqual(hash_to_password(final_hash), expected)


if __name__ == "__main__":
    unittest.main()
