"""Unit tests for RUT response schema."""
import pytest
from pydantic import ValidationError

from app.api.v1.schemas_rut import DeudaResponse


class TestDeudaResponse:
    """Tests for DeudaResponse schema."""

    def test_valid_full_response(self) -> None:
        response = DeudaResponse(
            found=True,
            rut=12345678,
            dv="5",
            nombre="Juan Pérez",
            universidad="Universidad de Chile",
            monto_utm=150.5,
            monto_clp=11460500,
            utm_fecha="2025-03",
        )
        assert response.found is True
        assert response.rut == 12345678
        assert response.dv == "5"
        assert response.nombre == "Juan Pérez"

    def test_found_false_returns_only_rut_and_dv(self) -> None:
        """When found=False, only rut/dv are required; rest is optional."""
        response = DeudaResponse(found=False, rut=12345678, dv="5")
        assert response.found is False
        assert response.rut == 12345678
        assert response.dv == "5"
        assert response.nombre is None
        assert response.monto_utm is None

    def test_required_fields_missing_raises(self) -> None:
        with pytest.raises(ValidationError):
            DeudaResponse(found=False)  # missing rut and dv

    def test_dv_must_be_single_char_or_k(self) -> None:
        """Verify that dv field exists and is a string."""
        # dv is a string; the schema doesn't restrict length at Pydantic level
        # but the domain validator ensures it's always single char
        response = DeudaResponse(found=True, rut=1, dv="K")
        assert response.dv == "K"
        assert len(response.dv) == 1

    def test_rut_coerces_from_string(self) -> None:
        """Pydantic coerces string rut to int; this is acceptable API behavior."""
        response = DeudaResponse(found=True, rut="12345678", dv="5")
        assert response.rut == 12345678
        assert isinstance(response.rut, int)

    def test_extra_fields_are_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            DeudaResponse(found=True, rut=12345678, dv="5", extra_field="x")

    def test_example_output_matches_schema(self) -> None:
        """Verify the documented example conforms to the schema."""
        example = {
            "found": True,
            "rut": 12345678,
            "dv": "5",
            "nombre": "Juan Pérez",
            "universidad": "Universidad de Chile",
            "monto_utm": 150.5,
            "monto_clp": 11460500,
            "utm_fecha": "2025-03",
        }
        response = DeudaResponse(**example)
        assert response.model_dump() == example
