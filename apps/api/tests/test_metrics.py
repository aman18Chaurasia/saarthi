"""Tests for metrics.py Prometheus metrics aggregation."""
from metrics import MetricsCollector


def test_percentile_calculation():
    """Verify p50/p95 calculation correctness."""
    collector = MetricsCollector(max_samples=100)

    # Record 100 samples: 0, 10, 20, ..., 990
    for i in range(100):
        collector.record("asr", i * 10.0)

    p50 = collector.percentile("asr", 50)
    p95 = collector.percentile("asr", 95)

    assert 480 <= p50 <= 500  # 50th percentile ~490
    assert 940 <= p95 <= 950  # 95th percentile ~940


def test_ring_buffer_eviction():
    """Verify old samples are evicted when max_samples exceeded."""
    collector = MetricsCollector(max_samples=10)

    # Record 20 samples
    for i in range(20):
        collector.record("llm", float(i))

    # Should only keep last 10: [10, 11, ..., 19]
    assert len(collector.llm_samples) == 10
    assert min(collector.llm_samples) == 10.0
    assert max(collector.llm_samples) == 19.0


def test_prometheus_format():
    """Verify Prometheus exposition format output."""
    collector = MetricsCollector()
    collector.record("asr", 50.0)
    collector.record("asr", 100.0)
    collector.record("llm", 20.0)

    output = collector.prometheus_format()

    assert "saarthi_latency_ms" in output
    assert 'hop="asr"' in output
    assert 'hop="llm"' in output
    assert 'quantile="0.5"' in output
    assert 'quantile="0.95"' in output
    assert "saarthi_latency_ms_count" in output


def test_percentile_empty_samples():
    """Verify percentile returns 0.0 when no samples exist."""
    collector = MetricsCollector()
    assert collector.percentile("e2e", 50) == 0.0
    assert collector.percentile("e2e", 95) == 0.0
