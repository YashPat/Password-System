"""
Display strings for a running computation: percentage, speed, time spent,
time left and expected finish time.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta

from config import format_duration

_UNKNOWN = "—"


@dataclass(frozen=True)
class ProgressStats:
    fraction: float
    percent: str
    speed: str
    elapsed: str
    left: str
    finish: str


def progress_stats(done: int, total: int, elapsed: float, now: datetime) -> ProgressStats:
    """
    Turn raw progress numbers into display strings.

    Args:
        done: Iterations completed
        total: Total iterations
        elapsed: Seconds spent so far
        now: Current local time, used for the finish time

    Returns:
        ProgressStats with display-ready strings
    """
    fraction = done / total if total else 1.0

    if elapsed <= 0:
        speed = _UNKNOWN
    else:
        per_second = done / elapsed
        if per_second >= 1_000_000:
            speed = f"{per_second / 1_000_000:.1f}M hashes/s"
        else:
            speed = f"{per_second:,.0f} hashes/s"

    if done >= total:
        left, finish = "done", now.strftime("%H:%M")
    elif done == 0 or elapsed <= 0:
        left = finish = _UNKNOWN
    else:
        remaining = elapsed * (total - done) / done
        left = format_duration(remaining)
        finish_time = now + timedelta(seconds=remaining)
        finish = finish_time.strftime("%H:%M")
        days_ahead = (finish_time.date() - now.date()).days
        if days_ahead == 1:
            finish = f"tomorrow {finish}"
        elif days_ahead > 1:
            finish = f"in {days_ahead} days, {finish}"

    return ProgressStats(
        fraction=fraction,
        percent=f"{fraction * 100:.3f}%",
        speed=speed,
        elapsed=format_duration(elapsed),
        left=left,
        finish=finish,
    )
