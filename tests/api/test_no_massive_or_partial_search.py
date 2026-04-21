"""Tests to ensure no massive listings or partial search exist."""
import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Create a test client with a fresh app instance."""
    app = create_app()
    return TestClient(app)


class TestNoMassiveOrPartialSearch:
    """Verify the API contract prevents listings and partial searches."""

    def test_no_get_rut_list_endpoint(self, client: TestClient) -> None:
        """GET /v1/rut without path param should NOT exist (405 or 404)."""
        response = client.get("/v1/rut")
        assert response.status_code in (404, 405)

    def test_no_query_param_search(self, client: TestClient) -> None:
        """Passing ?rut=... should not be accepted as search mechanism."""
        response = client.get("/v1/rut?rut=12.345.678-5")
        # Either 404 (route not matched) or 400 (path param format error)
        assert response.status_code in (400, 404, 405)

    @pytest.mark.parametrize(
        "path",
        [
            "/v1/rut/",
            "/v1/rut/list",
            "/v1/rut/search",
            "/v1/rut/all",
        ],
    )
    def test_no_alternative_rut_paths(self, client: TestClient, path: str) -> None:
        """No alternative listing/search paths should be exposed.

        Note: due to path-parameter routing, /v1/rut/list etc. are matched
        as RUT values and rejected by validation (4xx) rather than 404.
        This is acceptable since no listing or partial search exists.
        """
        response = client.get(path)
        # Accept 404 (not matched) or 4xx (validation rejection)
        assert response.status_code in (400, 404, 405, 422)

    def test_post_on_rut_returns_405(self, client: TestClient) -> None:
        """POST should not be allowed on the RUT endpoint."""
        response = client.post("/v1/rut/12.345.678-5")
        assert response.status_code == 405

    def test_put_on_rut_returns_405(self, client: TestClient) -> None:
        """PUT should not be allowed on the RUT endpoint."""
        response = client.put("/v1/rut/12.345.678-5")
        assert response.status_code == 405

    def test_patch_on_rut_returns_405(self, client: TestClient) -> None:
        """PATCH should not be allowed on the RUT endpoint."""
        response = client.patch("/v1/rut/12.345.678-5")
        assert response.status_code == 405
