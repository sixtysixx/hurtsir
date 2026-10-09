from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field

from .config import Config

_PRUNE_THRESHOLD = 512


@dataclass(slots=True)
class RateLimiter:
    user_cooldown_s: float = 15.0
    channel_cooldown_s: float = 5.0
    max_per_minute: int = 10
    duplicate_window_s: float = 60.0
    window_s: float = 60.0
    now: Callable[[], float] = time.monotonic
    _last_by_user: dict[int, float] = field(default_factory=dict, init=False, repr=False)
    _last_by_channel: dict[int, float] = field(default_factory=dict, init=False, repr=False)
    _recent_keys: dict[tuple[int, str], float] = field(default_factory=dict, init=False, repr=False)
    _recent_sends: deque[float] = field(default_factory=deque, init=False, repr=False)

    @classmethod
    def from_config(
        cls, config: Config, now: Callable[[], float] = time.monotonic
    ) -> RateLimiter:
        """Single wiring point for the config -> limiter mapping (production and tests)."""
        return cls(
            user_cooldown_s=config.user_cooldown_s,
            channel_cooldown_s=config.channel_cooldown_s,
            max_per_minute=config.max_replies_per_minute,
            duplicate_window_s=config.duplicate_window_s,
            now=now,
        )

    def check(self, user_id: int, channel_id: int, key: str) -> str | None:
        now = self.now()
        last_user = self._last_by_user.get(user_id)
        if last_user is not None and now - last_user < self.user_cooldown_s:
            return "cooldown_user"
        last_channel = self._last_by_channel.get(channel_id)
        if last_channel is not None and now - last_channel < self.channel_cooldown_s:
            return "cooldown_channel"
        last_key = self._recent_keys.get((channel_id, key))
        if last_key is not None and now - last_key < self.duplicate_window_s:
            return "cooldown_duplicate"
        self._prune_sends(now)
        if len(self._recent_sends) >= self.max_per_minute:
            return "cooldown_global"
        return None

    def record(self, user_id: int, channel_id: int, key: str) -> None:
        now = self.now()
        self._last_by_user[user_id] = now
        self._last_by_channel[channel_id] = now
        self._recent_keys[(channel_id, key)] = now
        self._recent_sends.append(now)
        self._prune_sends(now)
        if len(self._last_by_user) > _PRUNE_THRESHOLD:
            self._prune_map(self._last_by_user, now, self.user_cooldown_s)
        if len(self._last_by_channel) > _PRUNE_THRESHOLD:
            self._prune_map(self._last_by_channel, now, self.channel_cooldown_s)
        if len(self._recent_keys) > _PRUNE_THRESHOLD:
            self._prune_map(self._recent_keys, now, self.duplicate_window_s)

    def release(self, user_id: int, channel_id: int, key: str) -> None:
        """Undo a recorded send whose reply was retracted.

        A vetoed reply no longer exists, so it must not keep the asker, the channel or that
        question locked out - otherwise retracting a wrong answer would prevent the corrected
        one from ever being sent. The per-minute volume counter is deliberately kept, so
        ask/veto cycles cannot exceed the normal reply budget.
        """
        self._last_by_user.pop(user_id, None)
        self._last_by_channel.pop(channel_id, None)
        self._recent_keys.pop((channel_id, key), None)

    def _prune_sends(self, now: float) -> None:
        sends = self._recent_sends
        while sends and now - sends[0] >= self.window_s:
            sends.popleft()

    @staticmethod
    def _prune_map(mapping: dict, now: float, window: float) -> None:
        for map_key, stamp in list(mapping.items()):
            if now - stamp >= window:
                del mapping[map_key]
        overflow = len(mapping) - _PRUNE_THRESHOLD
        if overflow > 0:
            for map_key, _ in sorted(mapping.items(), key=lambda item: item[1])[:overflow]:
                del mapping[map_key]
