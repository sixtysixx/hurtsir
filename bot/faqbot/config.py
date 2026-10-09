from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_USER_COOLDOWN_S = 15.0
DEFAULT_CHANNEL_COOLDOWN_S = 5.0
DEFAULT_MAX_REPLIES_PER_MINUTE = 10
DEFAULT_DUPLICATE_WINDOW_S = 60.0


@dataclass(frozen=True, slots=True)
class Config:
    token: str
    allowed_channel_ids: frozenset[int]
    csr_role_ids: frozenset[int]
    dry_run: bool
    user_cooldown_s: float
    channel_cooldown_s: float
    max_replies_per_minute: int
    duplicate_window_s: float


def _id_set(raw: str, var: str, noun: str) -> frozenset[int]:
    ids: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if not part.isdigit():
            raise SystemExit(f"{var}: {part!r} is not a {noun}")
        ids.add(int(part))
    return frozenset(ids)


def _seconds(raw: str | None, default: float) -> float:
    if raw is None or not raw.strip():
        return default
    try:
        value = float(raw)
    except ValueError:
        raise SystemExit(f"FAQ_COOLDOWN_S: {raw!r} is not a number") from None
    if value < 0:
        raise SystemExit("FAQ_COOLDOWN_S must not be negative")
    return value


def load_config(env: Mapping[str, str] | None = None) -> Config:
    env = os.environ if env is None else env
    token = (env.get("DISCORD_TOKEN") or "").strip()
    if not token:
        raise SystemExit(
            "DISCORD_TOKEN is not set. Copy bot/.env.example to bot/.env and paste your "
            "account token."
        )
    return Config(
        token=token,
        allowed_channel_ids=_id_set(
            env.get("FAQ_ALLOWED_CHANNEL_IDS") or "", "FAQ_ALLOWED_CHANNEL_IDS", "channel id"
        ),
        csr_role_ids=_id_set(env.get("FAQ_CSR_ROLE_IDS") or "", "FAQ_CSR_ROLE_IDS", "role id"),
        dry_run=(env.get("FAQ_DRY_RUN") or "").strip().lower() not in ("", "0", "false", "no"),
        user_cooldown_s=_seconds(env.get("FAQ_COOLDOWN_S"), DEFAULT_USER_COOLDOWN_S),
        channel_cooldown_s=DEFAULT_CHANNEL_COOLDOWN_S,
        max_replies_per_minute=DEFAULT_MAX_REPLIES_PER_MINUTE,
        duplicate_window_s=DEFAULT_DUPLICATE_WINDOW_S,
    )
