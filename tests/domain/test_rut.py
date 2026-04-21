"""Unit tests for Chilean RUT validation and normalization."""
import pytest

from app.domain.rut import parse_rut, _compute_dv, _normalize_input


class TestNormalizeInput:
    """Tests for _normalize_input helper."""

    def test_trims_external_spaces(self) -> None:
        assert _normalize_input("  12.345.678-5  ") == "12.345.678-5"

    def test_uppercases_k(self) -> None:
        assert _normalize_input("12345678k") == "12345678K"


class TestComputeDv:
    """Tests for _compute_dv helper."""

    @pytest.mark.parametrize(
        ("rut", "expected_dv"),
        [
            (12345678, "5"),
            (11111111, "1"),
            (22222222, "2"),
            (33333333, "3"),
            (44444444, "4"),
            (55555555, "5"),
            (66666666, "6"),
            (1234567, "4"),
            (10000000, "8"),
        ],
    )
    def test_compute_dv(self, rut: int, expected_dv: str) -> None:
        assert _compute_dv(rut) == expected_dv


class TestParseRut:
    """Tests for parse_rut function."""

    @pytest.mark.parametrize(
        ("raw", "expected_rut", "expected_dv"),
        [
            ("12345678-5", 12345678, "5"),
            ("12.345.678-5", 12345678, "5"),
            ("1000005-K", 1000005, "K"),
            ("1000005k", 1000005, "K"),  # lowercase k → normalized to K
            ("1000000-9", 1000000, "9"),
        ],
    )
    def test_valid_ruts(
        self, raw: str, expected_rut: int, expected_dv: str
    ) -> None:
        result = parse_rut(raw)
        assert result.rut == expected_rut
        assert result.dv == expected_dv

    @pytest.mark.parametrize(
        "raw",
        [
            "",
            "   ",
            "abc",
            "12.345.678",  # missing DV
            "-5",
            "1-9",  # too short for strict format
            "12-34-56-78-5",  # malformed separators
            "..12.345.678--5",  # malformed separators
            "12 345 678-5",  # internal spaces are not canonical
            "12345678-A",  # invalid DV letter
            "12345678-9",  # wrong DV
        ],
    )
    def test_invalid_ruts_raise(self, raw: str) -> None:
        with pytest.raises(ValueError):
            parse_rut(raw)

    def test_dv_case_insensitive(self) -> None:
        """'k' lowercased should be accepted and normalized to uppercase K."""
        result = parse_rut("1000005k")  # 1000005-K, lowercase k
        assert result.dv == "K"
        assert result.rut == 1000005

    @pytest.mark.parametrize(
        "raw",
        [
            "12345678-1",
            "12.345.678-3",
            "1.234.567-9",
        ],
    )
    def test_wrong_dv_raises(self, raw: str) -> None:
        with pytest.raises(ValueError) as exc_info:
            parse_rut(raw)
        assert "mismatch" in str(exc_info.value).lower()
