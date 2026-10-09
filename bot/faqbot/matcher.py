from __future__ import annotations

import re
from dataclasses import dataclass

from .faq import FAQ, PHRASE_WEIGHT, FaqEntry

_MENTION_RE = re.compile(r"<[@#][!&]?\d+>")
_NON_WORD_RE = re.compile(r"[^a-z0-9]+")

# Shorthand users type in the wild, mapped onto the spelling the FAQ data uses. Applied to
# every token of both the phrase lists and the incoming message, so "inj failed" and
# "inject failed" score identically (and "the exe wont run" still hits the bootstrapper entry).
_ALIASES: dict[str, str] = {
    "inj": "inject",
    "injs": "inject",
    "exec": "executor",
    "execs": "executor",
    "exe": "executor",
    "exes": "executor",
}


def _canonical(tokens: list[str]) -> list[str]:
    return [_ALIASES.get(token, token) for token in tokens]


def normalize(text: str) -> str:
    text = _MENTION_RE.sub(" ", text.lower())
    text = _NON_WORD_RE.sub(" ", text).strip()
    return " ".join(_canonical(text.split()))


def _present(haystack: str, phrase: str) -> bool:
    return f" {phrase} " in f" {haystack} "


@dataclass(frozen=True, slots=True)
class Match:
    entry: FaqEntry
    score: int


def _build_index(
    entries: tuple[FaqEntry, ...] = FAQ,
) -> tuple[tuple[FaqEntry, tuple[str, ...], frozenset[str]], ...]:
    index: list[tuple[FaqEntry, tuple[str, ...], frozenset[str]]] = []
    for entry in entries:
        phrases: list[str] = []
        seen: set[str] = set()
        for phrase in entry.phrases:
            normalized = normalize(phrase)
            if not normalized:
                raise ValueError(f"{entry.id}: phrase {phrase!r} normalizes to nothing")
            # aliases can collapse two spellings onto one phrase; count it once
            if normalized not in seen:
                seen.add(normalized)
                phrases.append(normalized)
        keywords: list[str] = []
        for keyword in entry.keywords:
            normalized = normalize(keyword)
            if not normalized or " " in normalized:
                raise ValueError(f"{entry.id}: keyword {keyword!r} is not a single token")
            keywords.append(normalized)
        index.append((entry, tuple(phrases), frozenset(keywords)))
    return tuple(index)


_INDEX = _build_index()


def match(text: str) -> Match | None:
    normalized = normalize(text)
    if not normalized:
        return None
    tokens = set(normalized.split())
    best: Match | None = None
    for entry, phrases, keywords in _INDEX:
        score = PHRASE_WEIGHT * sum(1 for p in phrases if _present(normalized, p))
        score += sum(1 for k in keywords if k in tokens)
        if score >= entry.min_score and (best is None or score > best.score):
            best = Match(entry, score)
    return best
