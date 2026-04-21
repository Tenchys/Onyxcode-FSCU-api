"""Tests for money conversion service."""
import pytest

from app.services.money import utm_to_clp


class TestUtmToClp:
    def test_basic_conversion(self):
        """Simple case: 1 UTM at 60000 CLP = 60000 CLP."""
        result = utm_to_clp(1.0, 60000.0)
        assert result == 60000.0

    def test_fractional_utm(self):
        """Fractional UTM amounts are correctly converted."""
        # 0.5 UTM * 60000 = 30000 CLP
        result = utm_to_clp(0.5, 60000.0)
        assert result == 30000.0

    def test_large_amount(self):
        """Large UTM amounts convert correctly."""
        result = utm_to_clp(150.5, 60000.0)
        assert result == 9030000.0

    def test_rounding_half_up(self):
        """Values exactly halfway round up."""
        # 0.5 UTM * 1 CLP = 0.5 -> rounds to 1
        result = utm_to_clp(0.5, 1.0)
        assert result == 1.0

    def test_negative_utm_raises(self):
        """Negative UTM amount raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            utm_to_clp(-1.0, 60000.0)

    def test_zero_utm_returns_zero(self):
        """Zero UTM returns zero CLP."""
        result = utm_to_clp(0.0, 60000.0)
        assert result == 0.0

    def test_zero_utm_value_raises(self):
        """Zero UTM value raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            utm_to_clp(100.0, 0.0)

    def test_negative_utm_value_raises(self):
        """Negative UTM value raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            utm_to_clp(100.0, -50000.0)

    def test_precision_no_binary_errors(self):
        """No floating point accumulation errors."""
        # 10 * 60000 = 600000 exactly
        result = utm_to_clp(10.0, 60000.0)
        assert result == 600000.0

    def test_decimal_precision(self):
        """Handles typical UTM values with precision."""
        # 100.25 UTM * 60000.52 CLP = 6015052.38 -> rounds to 6015052
        result = utm_to_clp(100.25, 60000.52)
        assert result == 6015052.0