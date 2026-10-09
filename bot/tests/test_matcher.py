from __future__ import annotations

import pytest

from faqbot.faq import FAQ, FOOTER, HELP, FaqEntry
from faqbot.handler import compose_reply
from faqbot.matcher import _ALIASES, _build_index, _INDEX, match, normalize

CASES: tuple[tuple[str, str | None], ...] = (
    ("how do I fix unsupported version", "unsupported-version"),
    ("UNSUPPORTED VERSION!!!", "unsupported-version"),
    ("it says version check fails", "unsupported-version"),
    ("antivirus keeps deleting it", "antivirus"),
    ("windows defender flagged it as a trojan", "antivirus"),
    ("the bootstrapper closes instantly", "bootstrapper-hang"),
    ("inject failed", "injection-failed"),
    ("nothing happens when i click inject", "injection-failed"),
    ("my script wont execute", "scripts-dont-run"),
    ("roblox is a black screen", "roblox-wont-launch"),
    ("is minimize to tray a problem", "roblox-settings"),
    ("am i on the right windows version", "windows-version"),
    ("missing dll error", "prerequisites"),
    ("the cleaner logged me out", "cleaner-auth"),
    ("thingamabob download fails", "rdd-download-fails"),
    ("unsupported", None),
    ("hello everyone", None),
    ("when does the new season start", None),
    # tuned phrasings: these all missed before the phrase lists were expanded
    ("how do i downgrade", "unsupported-version"),
    ("how do i downgrade roblox", "unsupported-version"),
    ("how to downgrade", "unsupported-version"),
    ("downgrade guide?", "unsupported-version"),
    ("what build should i downgrade to", "unsupported-version"),
    ("it says waiting for roblox to open", "injection-failed"),
    ("stuck on waiting for roblox", "injection-failed"),
    ("failed to attach", "injection-failed"),
    ("it says failed to attach to roblox", "injection-failed"),
    ("the exe wont run", "bootstrapper-hang"),
    ("the bootstrapper wont even open", "bootstrapper-hang"),
    ("antivirus quarantined the bootstrapper", "antivirus"),
    ("defender deleted robloxplayerbeta", "antivirus"),
    ("executor says script error", "scripts-dont-run"),
    ("script gave an error", "scripts-dont-run"),
    ("i need to reinstall roblox", "roblox-wont-launch"),
    ("which version of windows", "windows-version"),
    ("do i need vc++ x86", "prerequisites"),
    ("the cleaner made me log in again", "cleaner-auth"),
    ("my login got reset", "cleaner-auth"),
    ("my login was wiped", "cleaner-auth"),
    # account / suspension
    ("i got banned", "account-suspended"),
    ("am i banned", "account-suspended"),
    ("why was i banned", "account-suspended"),
    ("my account got suspended", "account-suspended"),
    ("my account was banned", "account-suspended"),
    ("ban appeal", "account-suspended"),
    ("unban me", "account-suspended"),
    ("i think i have an hwid ban", "account-suspended"),
    ("how do i contact support", "account-suspended"),
    ("i want to open a ticket", "account-suspended"),
    # billing / product key
    ("where is my key", "billing-issues"),
    ("i didn't get my key", "billing-issues"),
    ("lost my key", "billing-issues"),
    ("my product key doesn't work", "billing-issues"),
    ("invalid key", "billing-issues"),
    ("i have my selly id", "billing-issues"),
    ("is there a tracking page", "billing-issues"),
    ("payment went through but nothing", "billing-issues"),
    ("i got charged twice", "billing-issues"),
    ("refund please", "billing-issues"),
    ("i bought sirhurt and never got a key", "billing-issues"),
    # shorthand spellings the alias layer folds onto the FAQ data's wording
    ("inj failed", "injection-failed"),
    ("inj", "injection-failed"),
    ("my inj is stuck", "injection-failed"),
    ("inj failed to attach", "injection-failed"),
    ("exec error", "scripts-dont-run"),
    ("script exec error", "scripts-dont-run"),
    ("exe closes instantly", "bootstrapper-hang"),
    ("exe wont open", "bootstrapper-hang"),
    ("the exe wont even open", "bootstrapper-hang"),
)


@pytest.mark.parametrize(("text", "expected"), CASES)
def test_match_table(text: str, expected: str | None) -> None:
    hit = match(text)
    assert (None if hit is None else hit.entry.id) == expected


def test_mention_is_stripped_before_matching() -> None:
    hit = match("<@123456789012345678> inject failed")
    assert hit is not None
    assert hit.entry.id == "injection-failed"


@pytest.mark.parametrize("entry", FAQ, ids=lambda entry: entry.id)
def test_composed_answer_fits_discord(entry) -> None:
    """The reply that actually gets sent is answer + footer, so check that, not the body."""
    assert len(compose_reply(entry.answer)) <= 1900


def test_composed_help_fits_discord() -> None:
    assert len(compose_reply(HELP)) <= 1900


def test_footer_is_small_text_and_mentions_csr() -> None:
    assert FOOTER.startswith("-# ")
    assert "automated reply" in FOOTER
    assert "pinned messages" in FOOTER
    assert "CSR" in FOOTER


def test_footer_lives_on_one_logical_line() -> None:
    """A wrapped footer would push the subtext marker onto its own line."""
    assert "\n" not in FOOTER


def test_empty_text_matches_nothing() -> None:
    assert match("") is None
    assert match("   ") is None


@pytest.mark.parametrize("entry", FAQ, ids=lambda entry: entry.id)
def test_entry_shape(entry) -> None:
    assert entry.phrases, f"{entry.id} has no phrases"
    assert entry.keywords, f"{entry.id} has no keywords"
    assert entry.title
    assert len(entry.answer) <= 1900, f"{entry.id} answer is too long for Discord"


def test_help_is_within_limit() -> None:
    assert len(HELP) <= 1900


def test_entry_ids_are_unique() -> None:
    ids = [entry.id for entry in FAQ]
    assert len(ids) == len(set(ids))


CHATTER: tuple[str, ...] = (
    "yo does anyone know when the next update drops",
    "how much does sirhurt cost",
    "anyone got a good script for bedwars",
    "bro my wifi is so bad",
    "is sirhurt detected?",
    "can someone help me log in",
    "where do i download this",
    "gonna update my drivers tomorrow",
    "should i downgrade my gpu drivers",
    "my scores got reset",
    "the download gave an error",
    "i've been waiting to open my case",
    "my game wont run",
    "can i get banned using this",
    "my discord account got banned",
    "whats the cost of a key",
    "anyone got a spare key for the event",
    "i bought minecraft today",
    "i need to reorder my playlist",
    "in order to fix this what do i do",
    "anyone know a good scripting key system",
    "my keyboard is broken",
    "the script has no key",
    "my exe file is corrupted",
    "the exe is in my downloads folder",
    "i need to exec a plan",
    "my score got exec",
    "how do i attach a file to this",
    "injury report",
    "lol that clip was insane",
)


@pytest.mark.parametrize("text", CHATTER)
def test_chatter_stays_silent(text: str) -> None:
    assert match(text) is None, f"{text!r} should not trigger a FAQ reply"


def test_aliases_are_folded_in_normalize() -> None:
    assert normalize("INJ!!") == "inject"
    assert normalize("the EXE wont run") == "the executor wont run"
    assert normalize("<@123> exec") == "executor"


def test_alias_targets_exist_in_the_faq_data() -> None:
    """A target nothing matches would silently make the alias a no-op."""
    data: set[str] = set()
    for entry in FAQ:
        data.update(normalize(phrase) for phrase in entry.phrases)
        data.update(normalize(keyword) for keyword in entry.keywords)
    for shorthand, target in _ALIASES.items():
        assert target in data, f"{shorthand!r} maps to {target!r}, which no entry matches on"


def test_colliding_spellings_do_not_double_count() -> None:
    """Two spellings that fold onto one phrase must score once, not twice."""
    entry = FaqEntry(
        id="synthetic",
        title="synthetic",
        phrases=("exe wont run", "executor wont run"),
        keywords=("run", "run"),
        answer="x",
    )
    ((built, phrases, keywords),) = _build_index((entry,))
    assert built is entry
    assert phrases == ("executor wont run",)
    assert keywords == frozenset({"run"})


def test_shorthand_and_full_spelling_score_identically() -> None:
    shorthand = match("inj failed")
    full = match("inject failed")
    assert shorthand is not None and full is not None
    assert shorthand.entry.id == full.entry.id == "injection-failed"
    assert shorthand.score == full.score
