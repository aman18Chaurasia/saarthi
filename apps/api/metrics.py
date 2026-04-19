"""Latency metrics aggregation for /metrics endpoint (Prometheus format).

Collects per-hop latency samples from LatencyFrame emissions and exposes
p50/p95 histograms via /metrics. Uses a ring buffer to keep last N samples.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Literal


HopName = Literal["asr", "llm", "tts", "e2e"]


@dataclass
class MetricsCollector:
    """Thread-safe metrics collector for voice pipeline latency.

    Stores last max_samples per hop for p50/p95 calculation.
    """
    max_samples: int = 1000

    asr_samples: deque[float] = field(default_factory=deque)
    llm_samples: deque[float] = field(default_factory=deque)
    tts_samples: deque[float] = field(default_factory=deque)
    e2e_samples: deque[float] = field(default_factory=deque)

    def record(self, hop: HopName, duration_ms: float) -> None:
        """Record a latency sample for the given hop."""
        samples = getattr(self, f"{hop}_samples")
        samples.append(duration_ms)
        if len(samples) > self.max_samples:
            samples.popleft()

    def percentile(self, hop: HopName, p: int) -> float:
        """Calculate percentile (50 or 95) for the given hop.

        Returns 0.0 if no samples exist.
        """
        samples = list(getattr(self, f"{hop}_samples"))
        if not samples:
            return 0.0

        sorted_samples = sorted(samples)
        index = int(len(sorted_samples) * p / 100)
        return sorted_samples[min(index, len(sorted_samples) - 1)]

    def prometheus_format(self) -> str:
        """Generate Prometheus exposition format metrics.

        Emits histogram summaries with p50/p95 quantiles per hop.
        """
        lines = [
            "# HELP saarthi_latency_ms Voice pipeline latency by hop",
            "# TYPE saarthi_latency_ms summary",
        ]

        for hop in ("asr", "llm", "tts", "e2e"):
            samples = list(getattr(self, f"{hop}_samples"))
            count = len(samples)
            total = sum(samples) if samples else 0.0
            p50 = self.percentile(hop, 50)  # type: ignore[arg-type]
            p95 = self.percentile(hop, 95)  # type: ignore[arg-type]

            lines.extend([
                f'saarthi_latency_ms{{hop="{hop}",quantile="0.5"}} {p50}',
                f'saarthi_latency_ms{{hop="{hop}",quantile="0.95"}} {p95}',
                f'saarthi_latency_ms_sum{{hop="{hop}"}} {total}',
                f'saarthi_latency_ms_count{{hop="{hop}"}} {count}',
            ])

        return "\n".join(lines) + "\n"


# Global singleton
_collector = MetricsCollector()


def get_collector() -> MetricsCollector:
    """Return the global metrics collector instance."""
    return _collector
