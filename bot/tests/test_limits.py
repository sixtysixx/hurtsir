from __future__ import annotations

from faqbot.limits import RateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.value = 1000.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def _limiter() -> tuple[RateLimiter, FakeClock]:
    clock = FakeClock()
    return RateLimiter(now=clock), clock


def test_user_cooldown_then_expiry() -> None:
    limiter, clock = _limiter()
    limiter.record(1, 10, "antivirus")
    assert limiter.check(1, 10, "antivirus") == "cooldown_user"
    clock.advance(15)
    assert limiter.check(1, 10, "prerequisites") is None
    assert limiter.check(1, 10, "antivirus") == "cooldown_duplicate"
    clock.advance(1)
    assert limiter.check(1, 10, "prerequisites") is None


def test_user_cooldown_boundary_just_under() -> None:
    limiter, clock = _limiter()
    limiter.record(1, 10, "antivirus")
    clock.advance(14.9)
    assert limiter.check(1, 10, "antivirus") == "cooldown_user"


def test_channel_cooldown_for_other_user() -> None:
    limiter, clock = _limiter()
    limiter.record(1, 10, "antivirus")
    clock.advance(2)
    assert limiter.check(2, 10, "prerequisites") == "cooldown_channel"
    clock.advance(5)
    assert limiter.check(2, 10, "prerequisites") is None


def test_duplicate_key_in_same_channel() -> None:
    limiter, clock = _limiter()
    limiter.record(1, 10, "antivirus")
    clock.advance(30)
    assert limiter.check(2, 10, "antivirus") == "cooldown_duplicate"
    clock.advance(30)
    assert limiter.check(2, 10, "antivirus") is None


def test_duplicate_key_is_per_channel() -> None:
    limiter, clock = _limiter()
    limiter.record(1, 10, "antivirus")
    clock.advance(30)
    assert limiter.check(2, 11, "antivirus") is None


def test_global_limit_and_sliding_window() -> None:
    limiter, clock = _limiter()
    for index in range(10):
        assert limiter.check(index, index, f"key{index}") is None
        limiter.record(index, index, f"key{index}")
    assert limiter.check(99, 99, "fresh") == "cooldown_global"
    clock.advance(61)
    assert limiter.check(99, 99, "fresh") is None


def test_pruning_keeps_user_map_bounded() -> None:
    limiter, clock = _limiter()
    for user_id in range(600):
        limiter.record(user_id, 1, f"key{user_id}")
        clock.advance(1)
    assert len(limiter._last_by_user) <= 512


def test_pruning_drops_expired_entries() -> None:
    limiter, clock = _limiter()
    for user_id in range(600):
        limiter.record(user_id, 1, f"key{user_id}")
    clock.advance(61)
    for user_id in range(600, 1200):
        limiter.record(user_id, 1, f"key{user_id}")
    assert len(limiter._last_by_user) <= 512


def test_pruning_keeps_recent_key_map_bounded() -> None:
    limiter, clock = _limiter()
    for index in range(600):
        limiter.record(1, index, "antivirus")
        clock.advance(0.1)
    assert len(limiter._recent_keys) <= 512
