"""UTM API client with timeout and robust parsing."""
import logging
from dataclasses import dataclass

import httpx
from pydantic import BaseModel

from app.core.settings import get_settings

logger = logging.getLogger(__name__)


class UtmValue(BaseModel):
    """UTM value with reference date."""

    utm: float
    fecha: str  # YYYY-MM format


class UtmApiError(Exception):
    """Raised when the UTM API is unreachable, times out, or returns malformed data."""


class UtmParseError(UtmApiError):
    """Raised when the UTM response cannot be parsed."""


@dataclass(frozen=True)
class UtmResult:
    """Result of fetching UTM value."""

    success: bool
    value: UtmValue | None = None
    error_message: str | None = None


async def fetch_utm_value() -> UtmResult:
    """Fetch current UTM value from external API.

    Returns UtmResult with success=True and UtmValue on valid response.
    Returns UtmResult with success=False and error_message on any failure.

    Failure scenarios:
    - Connection error
    - HTTP non-2xx status
    - Timeout
    - Malformed JSON / unexpected payload structure
    """
    settings = get_settings()
    url = settings.utm_api_url
    timeout = settings.utm_request_timeout_seconds

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout)
            response.raise_for_status()
            data = response.json()

        # Expected structure: {"data": [{"value": 12345.67, "date": "2025-03"}]}
        if not isinstance(data, dict):
            return UtmResult(
                success=False,
                error_message="Unexpected payload type, expected dict",
            )

        data_list = data.get("data")
        if not isinstance(data_list, list) or len(data_list) == 0:
            return UtmResult(
                success=False,
                error_message="Missing or empty 'data' array in response",
            )

        first_entry = data_list[0]
        if not isinstance(first_entry, dict):
            return UtmResult(
                success=False,
                error_message="First 'data' entry is not an object",
            )

        raw_utm = first_entry.get("value")
        raw_fecha = first_entry.get("date")

        if raw_utm is None or raw_fecha is None:
            return UtmResult(
                success=False,
                error_message=f"Missing 'value' or 'date' fields: {first_entry}",
            )

        utm_float = float(raw_utm)
        fecha_str = str(raw_fecha).strip()

        return UtmResult(
            success=True,
            value=UtmValue(utm=utm_float, fecha=fecha_str),
        )

    except httpx.TimeoutException:
        logger.warning("UTM API request timed out after %s seconds", timeout)
        return UtmResult(success=False, error_message="UTM API timeout")
    except httpx.HTTPStatusError as exc:
        logger.warning("UTM API returned HTTP %s: %s", exc.response.status_code, exc)
        return UtmResult(success=False, error_message=f"UTM API HTTP error {exc.response.status_code}")
    except (ValueError, TypeError) as exc:
        logger.warning("UTM API parse error: %s", exc)
        return UtmResult(success=False, error_message=f"UTM parse error: {exc}")
    except Exception as exc:
        logger.error("UTM API unexpected error: %s", exc)
        return UtmResult(success=False, error_message=f"UTM API unexpected error: {exc}")