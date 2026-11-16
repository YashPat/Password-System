"""Tests for the progress stats shown on the computing screen."""
import unittest
from datetime import datetime

from progress import progress_stats

NOW = datetime(2026, 11, 15, 22, 0)


class ProgressStatsTest(unittest.TestCase):
    def test_midway(self):
        stats = progress_stats(50, 100, 3600.0, NOW)
        self.assertEqual(stats.fraction, 0.5)
        self.assertEqual(stats.percent, "50.000%")
        self.assertEqual(stats.elapsed, "1h 00m")
        self.assertEqual(stats.left, "1h 00m")
        self.assertEqual(stats.finish, "23:00")
        self.assertEqual(stats.speed, "0 hashes/s")

    def test_speed_millions(self):
        stats = progress_stats(6_400_000, 100_000_000, 1.0, NOW)
        self.assertEqual(stats.speed, "6.4M hashes/s")

    def test_zero_elapsed(self):
        stats = progress_stats(0, 100, 0.0, NOW)
        self.assertEqual(stats.fraction, 0.0)
        self.assertEqual(stats.left, "—")
        self.assertEqual(stats.finish, "—")
        self.assertEqual(stats.speed, "—")

    def test_finished(self):
        stats = progress_stats(100, 100, 10.0, NOW)
        self.assertEqual(stats.percent, "100.000%")
        self.assertEqual(stats.left, "done")

    def test_finish_next_day(self):
        # 3600 s * (2870 - 300) / 300 = 30840 s = 8h 34m left; 22:10 + 8h34m = 06:44
        stats = progress_stats(300, 2870, 3600.0, datetime(2026, 11, 15, 22, 10))
        self.assertEqual(stats.left, "8h 34m")
        self.assertEqual(stats.finish, "tomorrow 06:44")


if __name__ == "__main__":
    unittest.main()
