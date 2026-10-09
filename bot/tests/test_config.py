from __future__ import annotations

import pytest

from faqbot.config import (
    DEFAULT_MAX_REPLIES_PER_MINUTE,
    DEFAULT_USER_COOLDOWN_S,
    load_config,
)

MINIMAL = {"DISCORD_TOKEN": "abc"}


def test_minimal_env_gets_defaults() -> None:
    config = load_config(MINIMAL)
    assert config.token == "abc"
    assert config.allowed_channel_ids == frozenset()
    assert config.csr_role_ids == frozenset()
    assert config.dry_run is False
    assert config.user_cooldown_s == DEFAULT_USER_COOLDOWN_S
    assert config.max_replies_per_minute == DEFAULT_MAX_REPLIES_PER_MINUTE


def test_missing_token_exits() -> None:
    with pytest.raises(SystemExit) as excinfo:
        load_config({})
    assert "DISCORD_TOKEN is not set" in str(excinfo.value)


def test_blank_token_exits() -> None:
    with pytest.raises(SystemExit):
        load_config({"DISCORD_TOKEN": "   "})


def test_token_is_stripped() -> None:
    assert load_config({"DISCORD_TOKEN": " abc "}).token == "abc"


@pytest.mark.parametrize("raw", ["1,2", " 1 , 2 ", "1,,2"])
def test_channel_ids_parse(raw: str) -> None:
    assert load_config({**MINIMAL, "FAQ_ALLOWED_CHANNEL_IDS": raw}).allowed_channel_ids == frozenset(
        {1, 2}
    )


def test_channel_ids_reject_junk() -> None:
    with pytest.raises(SystemExit) as excinfo:
        load_config({**MINIMAL, "FAQ_ALLOWED_CHANNEL_IDS": "abc"})
    assert str(excinfo.value) == "FAQ_ALLOWED_CHANNEL_IDS: 'abc' is not a channel id"


def test_csr_role_ids_parse() -> None:
    config = load_config({**MINIMAL, "FAQ_CSR_ROLE_IDS": "500, 501"})
    assert config.csr_role_ids == frozenset({500, 501})


def test_csr_role_ids_default_to_empty() -> None:
    assert load_config(MINIMAL).csr_role_ids == frozenset()
    assert load_config({**MINIMAL, "FAQ_CSR_ROLE_IDS": ""}).csr_role_ids == frozenset()


def test_csr_role_ids_reject_junk() -> None:
    with pytest.raises(SystemExit) as excinfo:
        load_config({**MINIMAL, "FAQ_CSR_ROLE_IDS": "500,ops"})
    assert str(excinfo.value) == "FAQ_CSR_ROLE_IDS: 'ops' is not a role id"


@pytest.mark.parametrize("raw", ["1", "true", "TRUE", "yes"])
def test_dry_run_truthy(raw: str) -> None:
    assert load_config({**MINIMAL, "FAQ_DRY_RUN": raw}).dry_run is True


@pytest.mark.parametrize("raw", ["", "0", "false", "no"])
def test_dry_run_falsy(raw: str) -> None:
    assert load_config({**MINIMAL, "FAQ_DRY_RUN": raw}).dry_run is False


def test_cooldown_parses() -> None:
    assert load_config({**MINIMAL, "FAQ_COOLDOWN_S": "2.5"}).user_cooldown_s == 2.5


def test_cooldown_rejects_junk() -> None:
    with pytest.raises(SystemExit) as excinfo:
        load_config({**MINIMAL, "FAQ_COOLDOWN_S": "soon"})
    assert "is not a number" in str(excinfo.value)


def test_cooldown_rejects_negative() -> None:
    with pytest.raises(SystemExit):
        load_config({**MINIMAL, "FAQ_COOLDOWN_S": "-1"})
