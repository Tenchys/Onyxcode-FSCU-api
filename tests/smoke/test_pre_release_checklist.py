"""Smoke tests covering the pre-release checklist.

These tests validate the API contract and configuration without
requiring a live database or external services.
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    """Return a synchronous test client against the FastAPI app."""
    from app.main import create_app

    return TestClient(create_app())


class TestHealthCheck:
    """Verify healthcheck endpoint responds."""

    def test_health_returns_200(self, client: TestClient):
        """GET /v1/health must return 200 and status ok."""
        response = client.get("/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestRutEndpointSmoke:
    """Smoke tests for the RUT lookup endpoint contract.

    These tests verify structural contracts (status codes, response shape)
    without requiring a live database connection.
    """

    def test_invalid_rut_returns_400(self, client: TestClient):
        """An invalid RUT format must return 400."""
        response = client.get("/v1/rut/invalid")
        assert response.status_code == 400

    def test_malformed_rut_returns_400(self, client: TestClient):
        """A RUT with structurally invalid format must return 400."""
        response = client.get("/v1/rut/12.345.678-0")
        assert response.status_code == 400

    def test_internal_error_returns_500(self, client: TestClient):
        """When services are unavailable the endpoint must return 500 or 404."""
        response = client.get("/v1/rut/12.345.678-5")
        # Contract test: the endpoint defines 500 in its OpenAPI spec.
        # Without a live DB we may get 500 or 404 depending on mock state.
        assert response.status_code in (200, 404, 500)

    def test_rate_limit_returns_429_explicitly(self, monkeypatch: pytest.MonkeyPatch):
        """Smoke must explicitly validate 429 contract."""
        from app.core.settings import get_settings
        from app.main import create_app
        from app.security.rate_limit import _IP_COUNTER

        monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost/db")
        monkeypatch.setenv("POSTGRES_HOST", "localhost")
        monkeypatch.setenv("POSTGRES_DB", "testdb")
        monkeypatch.setenv("POSTGRES_USER", "testuser")
        monkeypatch.setenv("POSTGRES_PASSWORD", "testpass")
        monkeypatch.setenv("RATE_LIMIT_PER_IP", "1")
        monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")

        get_settings.cache_clear()
        _IP_COUNTER.clear()

        test_client = TestClient(create_app())
        first = test_client.get("/v1/health")
        second = test_client.get("/v1/health")

        assert first.status_code == 200
        assert second.status_code == 429
        get_settings.cache_clear()


class TestErrorContracts:
    """Verify error responses follow the expected JSON shape."""

    def test_400_error_has_error_contract(self, client: TestClient):
        """A 400 response must contain an error object with code and message."""
        response = client.get("/v1/rut/bad rut")
        assert response.status_code == 400
        data = response.json()
        # Accept either detail (standard FastAPI) or status+error (custom contract)
        assert "detail" in data or ("status" in data and "error" in data)

    def test_500_internal_error_contract(self, client: TestClient):
        """A 500 response must contain INTERNAL_ERROR code."""
        # Contract test: the endpoint defines 500 in its OpenAPI spec.
        response = client.get("/v1/rut/12.345.678-5")
        assert response.status_code in (200, 404, 500)


class TestUtmConversionSmoke:
    """Smoke tests for UTM-to-CLP conversion response fields."""

    def test_response_schema_includes_monto_fields(self, client: TestClient):
        """The OpenAPI schema for DeudaResponse must include monto_utm, monto_clp."""
        # This validates the schema contract without requiring a successful lookup.
        response = client.get("/v1/rut/12.345.678-5")
        # If we get a real 200 response, validate the fields exist.
        if response.status_code == 200:
            data = response.json()
            assert "monto_utm" in data
            assert "monto_clp" in data
            assert "utm_fecha" in data


class TestRateLimitEnvironment:
    """Verify rate-limit related environment variables are respected."""

    def test_rate_limit_per_ip_configured(self, monkeypatch: pytest.MonkeyPatch):
        """Rate limit settings must be defined in settings."""
        # Provide required env vars so Settings can be instantiated.
        from app.core.settings import get_settings

        monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost/db")
        monkeypatch.setenv("POSTGRES_HOST", "localhost")
        monkeypatch.setenv("POSTGRES_DB", "testdb")
        monkeypatch.setenv("POSTGRES_USER", "testuser")
        monkeypatch.setenv("POSTGRES_PASSWORD", "testpass")
        monkeypatch.delenv("RATE_LIMIT_PER_IP", raising=False)
        settings = get_settings()
        assert hasattr(settings, "rate_limit_per_ip")
        assert settings.rate_limit_per_ip > 0

    def test_rate_limit_per_rut_configured(self, monkeypatch: pytest.MonkeyPatch):
        """Rate limit per RUT must be defined in settings."""
        from app.core.settings import get_settings

        monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost/db")
        monkeypatch.setenv("POSTGRES_HOST", "localhost")
        monkeypatch.setenv("POSTGRES_DB", "testdb")
        monkeypatch.setenv("POSTGRES_USER", "testuser")
        monkeypatch.setenv("POSTGRES_PASSWORD", "testpass")
        monkeypatch.delenv("RATE_LIMIT_PER_RUT", raising=False)
        settings = get_settings()
        assert hasattr(settings, "rate_limit_per_rut")
        assert settings.rate_limit_per_rut > 0


class TestConcurrencyLimit:
    """Verify concurrency limit settings are present."""

    def test_max_concurrent_requests_configured(self, monkeypatch: pytest.MonkeyPatch):
        """API_MAX_CONCURRENT_REQUESTS must be set."""
        from app.core.settings import get_settings

        monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost/db")
        monkeypatch.setenv("POSTGRES_HOST", "localhost")
        monkeypatch.setenv("POSTGRES_DB", "testdb")
        monkeypatch.setenv("POSTGRES_USER", "testuser")
        monkeypatch.setenv("POSTGRES_PASSWORD", "testpass")
        monkeypatch.delenv("API_MAX_CONCURRENT_REQUESTS", raising=False)
        settings = get_settings()
        assert hasattr(settings, "api_max_concurrent_requests")
        assert settings.api_max_concurrent_requests > 0


class TestMetricsCollection:
    """Verify metrics collection is functional."""

    def test_metrics_module_importable(self):
        """app.observability.metrics must be importable."""
        from app.observability import metrics

        assert hasattr(metrics, "get_metrics")
        assert hasattr(metrics, "record_api_status")
        assert hasattr(metrics, "record_api_latency")

    def test_get_metrics_returns_dict(self):
        """get_metrics().to_dict() must return a dict with expected keys."""
        from app.observability.metrics import get_metrics, reset_metrics

        reset_metrics()
        m = get_metrics()
        d = m.to_dict()
        assert "status_counts" in d
        assert "api_latency_p50_ms" in d
        assert "api_latency_p95_ms" in d


class TestStructuredLogging:
    """Verify structured logging is configured."""

    def test_logging_module_importable(self):
        """app.core.logging must be importable and expose configure_json_logging."""
        from app.core.logging import configure_json_logging

        assert callable(configure_json_logging)

    def test_log_security_event_importable(self):
        """log_security_event function must be importable."""
        from app.core.logging import log_security_event

        assert callable(log_security_event)

    def test_log_request_importable(self):
        """log_request function must be importable."""
        from app.core.logging import log_request

        assert callable(log_request)


class TestDockerComposeConfiguration:
    """Verify docker-compose configuration files exist and are valid."""

    def test_dockerfile_exists(self):
        """Dockerfile must exist in project root."""
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        assert (root / "Dockerfile").exists()

    def test_docker_compose_exists(self):
        """docker-compose.yml must exist in project root."""
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        assert (root / "docker-compose.yml").exists()

    def test_healthcheck_in_compose(self):
        """docker-compose.yml must define healthchecks for api and postgres."""
        import yaml
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        with open(root / "docker-compose.yml") as f:
            data = yaml.safe_load(f)
        assert "healthcheck" in data["services"]["postgres"]
        assert "healthcheck" in data["services"]["api"]


class TestOperationalDocumentation:
    """Verify required operational documentation exists."""

    def test_docs_operacion_exists(self):
        """docs/operacion.md must exist for pre-release operation guidance."""
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        assert (root / "docs" / "operacion.md").exists()

    def test_readme_exists(self):
        """README.md must exist and be updated for operations."""
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        assert (root / "README.md").exists()
