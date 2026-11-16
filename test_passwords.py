"""
Regression test: fixed recovery keys must always produce the same passwords.

Existing recovery keys depend on the exact hashing, so any change that alters
these outputs would make previously saved keys recover the wrong password.

Run with: python3 -m unittest test_passwords
"""
import contextlib
import io
import unittest

import config
from password_recovery import (
    ComputationCancelled,
    _perform_iterative_hashing,
    hash_to_password,
    recover_password,
)

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


class ProgressCallbackTest(unittest.TestCase):
    def test_callback_does_not_change_password(self):
        for seed, iterations, expected in KNOWN_KEYS:
            with self.subTest(iterations=iterations):
                password = recover_password(seed, iterations, on_progress=lambda *a: None)
                self.assertEqual(password, expected)

    def test_callback_reports_chunks(self):
        calls = []
        recover_password("ab" * 32, 12_000_000, on_progress=lambda *a: calls.append(a))
        self.assertEqual([done for done, _, _ in calls], [5_000_000, 10_000_000, 12_000_000])
        self.assertTrue(all(total == 12_000_000 for _, total, _ in calls))
        elapsed = [e for _, _, e in calls]
        self.assertEqual(elapsed, sorted(elapsed))

    def test_callback_single_iteration(self):
        calls = []
        recover_password("00" * 32, 1, on_progress=lambda *a: calls.append(a))
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][:2], (1, 1))

    def test_cancel_propagates(self):
        def cancel(*_):
            raise ComputationCancelled()

        with self.assertRaises(ComputationCancelled):
            recover_password("ab" * 32, 1000, on_progress=cancel)

    def test_callback_mode_prints_nothing(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            recover_password("ab" * 32, 1000, on_progress=lambda *a: None)
        self.assertEqual(out.getvalue(), "")

    def test_quiet_calibration(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            iterations = config.calibrate_iterations(1.0, verbose=False)
        self.assertEqual(out.getvalue(), "")
        self.assertIsInstance(iterations, int)
        self.assertGreater(iterations, 0)


if __name__ == "__main__":
    unittest.main()
