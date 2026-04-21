"""Chilean RUT validation and normalization."""
from dataclasses import dataclass
import re


_RUT_PATTERN = re.compile(
    r"^(?P<body>(?:\d{7,8}|\d{1,2}(?:\.\d{3}){2}))-?(?P<dv>[0-9Kk])$"
)


@dataclass(frozen=True)
class RutInfo:
    """Normalized RUT result."""

    rut: int  # Numeric part without DV
    dv: str  # Verifier digit (uppercase)


def _compute_dv(rut: int) -> str:
    """Compute the expected verifier digit for a given rut.

    Standard Chilean RUT algorithm: weights cycle 2..7 from rightmost digit.
    """
    rut_str = str(rut)
    sum_ = 0
    weight = 2
    for c in reversed(rut_str):
        sum_ += int(c) * weight
        weight = 2 if weight == 7 else weight + 1
    remainder = sum_ % 11
    if remainder == 0:
        return "0"
    if remainder == 1:
        return "K"
    return str(11 - remainder)


def _normalize_input(raw: str) -> str:
    """Trim external whitespace and normalize verifier digit casing."""
    return raw.strip().upper()


def parse_rut(raw: str) -> RutInfo:
    """Parse and validate a Chilean RUT string.

    Accepts formats like:
      - "12345678-5"
      - "12.345.678-5"
      - "12.345.678K"
      - "12345678K"

    Returns a normalized RutInfo with numeric rut and uppercase DV.
    Raises ValueError if the format is invalid or the DV does not match.
    """
    normalized = _normalize_input(raw)

    if not normalized:
        raise ValueError("RUT cannot be empty")

    match = _RUT_PATTERN.fullmatch(normalized)
    if match is None:
        raise ValueError(f"Invalid RUT format: {raw!r}")

    rut = int(match.group("body").replace(".", ""))
    dv_raw = match.group("dv").upper()

    # Determine expected DV
    expected_dv = dv_raw

    computed_dv = _compute_dv(rut)

    if computed_dv != expected_dv:
        raise ValueError(f"Verifier digit mismatch: expected {computed_dv}, got {expected_dv}")

    return RutInfo(rut=rut, dv=expected_dv)
