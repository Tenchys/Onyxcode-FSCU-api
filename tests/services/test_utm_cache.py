"""Tests for UTM cache service."""

from app.services.utm_cache import UtmCache
from app.integrations.utm_client import UtmValue


class MockTime:
    """Fakes time for deterministic tests."""

    def __init__(self, start: float = 1000.0):
        self._now = start

    def __call__(self) -> float:
        return self._now


def make_cache(ttl: int = 10, now: float = 1000.0) -> UtmCache:
    """Build cache with mocked clock."""
    cache = UtmCache(ttl_seconds=ttl)
    cache._now = MockTime(now)
    return cache


def utm(value: float = 60000.0, fecha: str = "2025-03") -> UtmValue:
    return UtmValue(utm=value, fecha=fecha)


class TestUtmCache:
    def test_miss_empty_cache(self):
        """No cache and no fallback returns None."""
        cache = make_cache(ttl=10, now=1000.0)
        value = cache.get_fresh()
        assert value is None
        assert cache.get_last_valid() is None

    def test_hit_fresh_entry(self):
        """Cached entry within TTL returns it as fresh."""
        cache = make_cache(ttl=10, now=1000.0)
        cache.set(utm(60000.0, "2025-03"))

        value = cache.get_fresh()

        assert value is not None
        assert value.utm == 60000.0
        assert cache.get_last_valid() is not None

    def test_expired_entry_forces_revalidation_but_keeps_fallback(self):
        """Expired cache must return None for fresh and preserve last_valid."""
        cache = make_cache(ttl=10, now=1000.0)
        cache.set(utm(60000.0, "2025-03"))
        cache._now._now = 1015.0  # Advance past TTL

        value = cache.get_fresh()
        fallback = cache.get_last_valid()

        assert value is None
        assert fallback is not None
        assert fallback.utm == 60000.0

    def test_miss_expired_no_fallback(self):
        """No stored value returns None for fresh and fallback."""
        cache = make_cache(ttl=10, now=1000.0)
        # Never set anything
        cache._now._now = 1020.0

        value = cache.get_fresh()

        assert value is None
        assert cache.get_last_valid() is None

    def test_set_updates_last_valid(self):
        """Setting a new value updates fallback."""
        cache = make_cache(ttl=10, now=1000.0)
        cache.set(utm(60000.0, "2025-03"))
        cache._now._now = 1015.0  # Expire
        cache.set(utm(61000.0, "2025-04"))
        cache._now._now = 1016.0

        value = cache.get_fresh()
        fallback = cache.get_last_valid()

        assert value is not None
        assert value.utm == 61000.0
        assert fallback is not None
        assert fallback.utm == 61000.0

    def test_clear(self):
        """Clear removes fresh entry but preserves last_valid fallback."""
        cache = make_cache(ttl=10, now=1000.0)
        cache.set(utm(60000.0, "2025-03"))
        cache.clear()

        value = cache.get_fresh()
        fallback = cache.get_last_valid()
        assert value is None
        assert fallback is not None
        assert fallback.utm == 60000.0
