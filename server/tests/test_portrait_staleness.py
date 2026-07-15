"""
Tests for app.portrait.stitcher.is_stale — the pure staleness function.

Run:  cd server && python -m pytest tests/ -v
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.portrait.stitcher import is_stale

NOW = datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)


def _at(days_ago: int) -> datetime:
    return NOW - timedelta(days=days_ago)


class TestIsStale:
    def test_never_generated_is_stale(self):
        assert is_stale(None, None, ["spotify", "github"], now=NOW) is True

    def test_fresh_same_set_is_not_stale(self):
        assert is_stale(_at(3), ["spotify", "github"], ["spotify", "github"], now=NOW) is False

    def test_provider_order_does_not_matter(self):
        assert is_stale(_at(3), ["github", "spotify"], ["spotify", "github"], now=NOW) is False

    def test_newly_connected_provider_is_stale(self):
        assert is_stale(_at(1), ["spotify"], ["spotify", "github"], now=NOW) is True

    def test_removed_provider_is_stale(self):
        assert is_stale(_at(1), ["spotify", "github"], ["spotify"], now=NOW) is True

    def test_just_under_ttl_is_not_stale(self):
        assert is_stale(_at(13), ["spotify", "gcal"], ["spotify", "gcal"], now=NOW) is False

    def test_over_ttl_is_stale(self):
        assert is_stale(_at(15), ["spotify", "gcal"], ["spotify", "gcal"], now=NOW) is True

    def test_custom_ttl(self):
        args = (_at(5), ["spotify", "gcal"], ["spotify", "gcal"])
        assert is_stale(*args, ttl_days=3, now=NOW) is True
        assert is_stale(*args, ttl_days=30, now=NOW) is False

    def test_naive_generated_at_treated_as_utc(self):
        naive = (NOW - timedelta(days=1)).replace(tzinfo=None)
        assert is_stale(naive, ["spotify", "gcal"], ["spotify", "gcal"], now=NOW) is False

    def test_empty_source_providers_with_connected_set_is_stale(self):
        assert is_stale(_at(1), [], ["spotify", "github"], now=NOW) is True
