"""Custom Pipecat frames for SAARTHI.

LatencyFrame carries per-hop timing so the metrics collector (commit 10)
can aggregate p50/p95 without needing direct access to processor internals.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from pipecat.frames.frames import DataFrame


@dataclass
class LatencyFrame(DataFrame):
    """Emitted by each I/O processor after it completes.

    Fields:
        hop: "asr" | "llm" | "tts"
        duration_ms: wall-clock time for this hop in milliseconds
    """
    hop: str = ""
    duration_ms: float = 0.0
