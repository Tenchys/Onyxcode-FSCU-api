"""RUT lookup orchestration service."""
import logging
from dataclasses import dataclass
from typing import Tuple

from app.core.settings import get_settings
from app.db.postgres import get_db_session
from app.integrations.utm_client import UtmValue, fetch_utm_value
from app.repositories.deudores_repo import DeudorRecord, find_deudor_by_rut
from app.services.money import utm_to_clp
from app.services.utm_cache import UtmCache

logger = logging.getLogger(__name__)

# Process-global cache instance (worker-scoped, not shared across processes)
_utm_cache: UtmCache | None = None


def _get_utm_cache() -> UtmCache:
    """Lazily create or return the process-global UTM cache."""
    global _utm_cache
    if _utm_cache is None:
        settings = get_settings()
        _utm_cache = UtmCache(ttl_seconds=settings.utm_cache_ttl_seconds)
    return _utm_cache


class DeudorNotFoundError(Exception):
    """Raised when no debtor matches the given RUT."""


class DatabaseError(Exception):
    """Raised on infrastructure failures (timeout, connection, etc.)."""


class UtmUnavailableError(Exception):
    """Raised when UTM API fails and there is no valid fallback."""


@dataclass(frozen=True)
class LookupResult:
    """Result of a RUT lookup operation."""

    found: bool
    rut: int
    dv: str
    nombre: str | None = None
    universidad: str | None = None
    monto_utm: float | None = None
    cod_universidad: int | None = None
    monto_clp: float | None = None
    utm_fecha: str | None = None


async def _fetch_utm_with_cache() -> Tuple[UtmValue, bool]:
    """Fetch UTM value using cache with fallback.

    Returns (utm_value, is_fresh) where is_fresh indicates
    whether the value is from a fresh API call (vs. fallback).
    """
    cache = _get_utm_cache()
    cached_value = cache.get_fresh()
    if cached_value is not None:
        return cached_value, True

    # Missing/expired cache — force remote revalidation
    result = await fetch_utm_value()
    if result.success and result.value is not None:
        cache.set(result.value)
        return result.value, True

    logger.warning("UTM API failed: %s", result.error_message)

    # Remote failed — use last valid fallback if available
    fallback = cache.get_last_valid()
    if fallback is not None:
        logger.info("Using last valid UTM fallback value")
        return fallback, False

    raise UtmUnavailableError("UTM value unavailable")


async def lookup_rut(rut: int, dv: str) -> LookupResult:
    """Look up an exact RUT+DV in the deudores table.

    Returns LookupResult with found=True and debtor data if present,
    including converted monto_clp from UTM.
    Returns LookupResult with found=False if no record matches.
    Raises DatabaseError on infrastructure failures.
    Raises UtmUnavailableError if UTM is needed but unavailable.
    """
    try:
        async with get_db_session() as session:
            record: DeudorRecord | None = await find_deudor_by_rut(session, rut, dv)
    except Exception as exc:
        raise DatabaseError(f"Database error during lookup: {exc}") from exc

    if record is None:
        return LookupResult(found=False, rut=rut, dv=dv)

    # Resolve UTM for conversion (mandatory for found records)
    utm_value, _ = await _fetch_utm_with_cache()

    monto_clp: float | None = None
    utm_fecha: str | None = None

    try:
        monto_clp = utm_to_clp(record.monto_utm, utm_value.utm)
        utm_fecha = utm_value.fecha
    except (ValueError, TypeError) as exc:
        logger.error("UTM conversion failed: %s", exc)
        raise UtmUnavailableError("UTM conversion error") from exc

    return LookupResult(
        found=True,
        rut=record.rut,
        dv=record.dv,
        nombre=record.nombre,
        universidad=record.universidad,
        monto_utm=record.monto_utm,
        cod_universidad=record.cod_universidad,
        monto_clp=monto_clp,
        utm_fecha=utm_fecha,
    )
