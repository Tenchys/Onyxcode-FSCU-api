"""Unit tests for metrics collection."""
import threading

import pytest
from fastapi.testclient import TestClient

from app.observability.metrics import (
    Metrics,
    get_metrics,
    record_api_latency,
    record_api_status,
    record_utm_latency,
    reset_metrics,
)


class TestRecordApiStatus:
    """Tests for record_api_status."""

    def test_increments_counter(self):
        """Calling record_api_status increments the count for that code."""
        reset_metrics()
        record_api_status(200)
        record_api_status(200)
        record_api_status(404)
        metrics = get_metrics()
        assert metrics.status_counts.get(200) == 2
        assert metrics.status_counts.get(404) == 1

    def test_4xx_and_5xx_tracked_separately(self):
        """4xx and 5xx codes must be tracked independently."""
        reset_metrics()
        record_api_status(429)
        record_api_status(500)
        record_api_status(500)
        metrics = get_metrics()
        assert metrics.status_counts.get(429) == 1
        assert metrics.status_counts.get(500) == 2


class TestRecordApiLatency:
    """Tests for record_api_latency."""

    def test_latency_sampled(self):
        """Latency samples must be stored and reflected in percentiles."""
        reset_metrics()
        for v in [10.0, 20.0, 30.0, 40.0, 50.0]:
            record_api_latency(v)
        metrics = get_metrics()
        assert metrics.api_latency_p50 is not None
        assert metrics.api_latency_p95 is not None

    def test_empty_returns_none_percentiles(self):
        """With no samples, percentiles must be None."""
        reset_metrics()
        metrics = get_metrics()
        assert metrics.api_latency_p50 is None
        assert metrics.api_latency_p95 is None


class TestRecordUtmLatency:
    """Tests for record_utm_latency."""

    def test_utm_latency_sampled(self):
        """UTM latency samples must be tracked separately from API latency."""
        reset_metrics()
        record_utm_latency(100.0)
        record_utm_latency(200.0)
        metrics = get_metrics()
        assert metrics.utm_latency_p50 is not None
        assert metrics.utm_latency_p95 is not None


class TestGetMetrics:
    """Tests for get_metrics snapshot."""

    def test_returns_metrics_object(self):
        """get_metrics must return a Metrics instance."""
        reset_metrics()
        metrics = get_metrics()
        assert isinstance(metrics, Metrics)

    def test_to_dict_contains_expected_keys(self):
        """to_dict() must expose all expected metric keys."""
        reset_metrics()
        record_api_status(200)
        metrics = get_metrics()
        d = metrics.to_dict()
        assert "status_counts" in d
        assert "api_latency_p50_ms" in d
        assert "api_latency_p95_ms" in d
        assert "utm_latency_p50_ms" in d
        assert "utm_latency_p95_ms" in d


class TestMetricsEndpoint:
    """Tests for `/metrics` publication."""

    def test_internal_metrics_endpoint_is_exposed(self):
        """Application must expose internal GET /metrics endpoint."""
        from app.main import create_app

        reset_metrics()
        record_api_status(429)
        record_api_latency(12.0)
        record_utm_latency(34.0)

        client = TestClient(create_app())
        response = client.get("/metrics")

        assert response.status_code == 200
        payload = response.json()
        assert "status_counts" in payload
        assert "api_latency_p50_ms" in payload
        assert "utm_latency_p50_ms" in payload


class TestResetMetrics:
    """Tests for reset_metrics."""

    def test_clears_all_counters(self):
        """reset_metrics must clear all status counts and latencies."""
        reset_metrics()
        record_api_status(500)
        record_api_latency(999.0)
        record_utm_latency(888.0)
        reset_metrics()
        metrics = get_metrics()
        assert metrics.status_counts == {}
        assert metrics.api_latency_p50 is None
        assert metrics.utm_latency_p50 is None

    def test_thread_safe(self):
        """reset_metrics must be safe to call from multiple threads."""
        reset_metrics()
        errors = []

        def worker():
            try:
                for _ in range(100):
                    record_api_status(200)
                    record_api_latency(1.0)
                    reset_metrics()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors
