"""Money conversion utilities — UTM to CLP with deterministic rounding."""
from decimal import ROUND_HALF_UP, Decimal


def utm_to_clp(monto_utm: float, utm_value: float) -> float:
    """Convert an amount in UTM to CLP using the given UTM exchange rate.

    Uses Decimal with ROUND_HALF_UP for consistent, reproducible results.
    Returns a float rounded to 0 decimal places (CLP has no cents).

    Args:
        monto_utm: Amount in UTM (e.g., 150.5)
        utm_value: Current UTM value in CLP (e.g., 60000.0)

    Returns:
        Equivalent amount in CLP as float.

    Example:
        >>> utm_to_clp(150.5, 60000.0)
        9030000.0
    """
    if monto_utm < 0:
        raise ValueError("monto_utm must be non-negative")
    if utm_value <= 0:
        raise ValueError("utm_value must be positive")

    amount = Decimal(str(monto_utm))
    rate = Decimal(str(utm_value))
    result = amount * rate

    # Round to 0 decimal places (CLP is whole pesos)
    rounded = result.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return float(rounded)