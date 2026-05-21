"""
Lightweight debug logging for runtime tracing.
"""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from typing import Iterator


def debug_enabled() -> bool:
    return os.getenv("SCRIPTA_DEBUG", "1").strip().lower() not in {"0", "false", "no", "off"}


def debug_log(stage: str, message: str) -> None:
    if not debug_enabled():
        return
    ts = time.strftime("%H:%M:%S")
    print(f"[Scripta {ts}] [{stage}] {message}", flush=True)


@contextmanager
def timed_stage(stage: str, message: str) -> Iterator[None]:
    debug_log(stage, f"{message} — start")
    t0 = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - t0
        debug_log(stage, f"{message} — done in {elapsed:.2f}s")
