"""
Run the hash computation in a separate process.

The hash loop keeps Python busy, so running it in a thread of the UI's own
process leaves the UI only brief turns and makes it lag by seconds. A child
process has its own interpreter, so the UI stays responsive and stopping is
instant (the process is terminated).

This uses subprocess rather than multiprocessing: multiprocessing needs a
real sys.stderr, which Textual replaces while the app runs. The seed goes to
the child over stdin, never on its command line, so it can't be seen in `ps`.
"""
import json
import os
import selectors
import subprocess
import sys
from typing import Callable

from password_recovery import (
    ComputationCancelled,
    ProgressCallback,
    _perform_iterative_hashing,
    hash_to_password,
)

# How often the parent checks for output and for a stop request
_POLL_SECONDS = 0.1


def compute_password(
    seed: str,
    iterations: int,
    on_progress: ProgressCallback,
    should_stop: Callable[[], bool],
) -> str:
    """
    Compute the password for (seed, iterations) in a child process. Blocks.

    Args:
        seed: Hex seed from the recovery keys
        iterations: Number of hash iterations
        on_progress: Called with (done, total, elapsed_seconds) in this process
        should_stop: Polled regularly; returning True stops the computation

    Returns:
        The password, identical to recover_password(seed, iterations)

    Raises:
        ComputationCancelled: If should_stop returned True
        RuntimeError: If the child process ended without a result
    """
    process = subprocess.Popen(
        [sys.executable, os.path.abspath(__file__)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
    try:
        process.stdin.write(json.dumps({"seed": seed, "iterations": iterations}))
        process.stdin.close()

        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        while True:
            if should_stop():
                raise ComputationCancelled()
            if not selector.select(_POLL_SECONDS):
                continue
            line = process.stdout.readline()
            if not line:
                raise RuntimeError("hashing process ended without a result")
            message = json.loads(line)
            if message["type"] == "progress":
                on_progress(message["done"], message["total"], message["elapsed"])
            else:
                return message["password"]
    finally:
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=5)
        process.stdout.close()


def _child_main() -> None:
    """Child side: read keys from stdin, hash, report progress as JSON lines."""
    keys = json.loads(sys.stdin.read())

    def send(message: dict) -> None:
        sys.stdout.write(json.dumps(message) + "\n")
        sys.stdout.flush()

    def report(done: int, total: int, elapsed: float) -> None:
        send({"type": "progress", "done": done, "total": total, "elapsed": elapsed})

    final_hash = _perform_iterative_hashing(
        bytes.fromhex(keys["seed"]), keys["iterations"], on_progress=report
    )
    send({"type": "done", "password": hash_to_password(final_hash)})


if __name__ == "__main__":
    _child_main()
