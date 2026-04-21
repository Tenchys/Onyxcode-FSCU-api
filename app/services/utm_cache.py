"""UTM in-process cache with TTL and fallback to last valid value."""
import logging
import time
from dataclasses import dataclass

from app.integrations.utm_client import UtmValue

logger = logging.getLogger(__name__)

# Sentinel for missing entry
_MISSING = object()


@dataclass(frozen=True)
class CachedUtm:
    """UTM value with cache metadata."""

    value: UtmValue
    fetched_at: float  # Unix timestamp when cached


class UtmCache:
    """In-process cache for UTM values with TTL and last-valid fallback.

    Thread-unsafe (async only, single event loop) — acceptable for FastAPI worker.
    """

    def __init__(self, ttl_seconds: int) -> None:
        """Initialize cache with given TTL in seconds."""
        self._ttl = ttl_seconds
        self._cache: dict[str, CachedUtm] = {}
        self._last_valid: UtmValue | None = None

    def _now(self) -> float:
        """Return current Unix timestamp. Override in tests."""
        return time.time()

    def _key(self) -> str:
        """Cache key is always the same since we only cache one UTM value."""
        return "utm"

    def get_fresh(self) -> UtmValue | None:
        """Return cached value only when still within TTL.

        When entry is expired, returns None so caller can force
        a real remote revalidation.
        """
        entry = self._cache.get(self._key(), _MISSING)
        if entry is _MISSING:
            return None

        age = self._now() - entry.fetched_at
        if age > self._ttl:
            logger.info("UTM cache expired; forcing remote revalidation")
            return None

        return entry.value

    def get_last_valid(self) -> UtmValue | None:
        """Return last known valid UTM value for fallback."""
        return self._last_valid

    def set(self, value: UtmValue) -> None:
        """Store UTM value in cache and update last valid."""
        self._cache[self._key()] = CachedUtm(value=value, fetched_at=self._now())
        self._last_valid = value
        logger.debug("UTM cached: %s (%s)", value.utm, value.fecha)

    def clear(self) -> None:
        """Invalidate all cached entries."""
        self._cache.clear()
        logger.debug("UTM cache cleared")
