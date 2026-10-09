from __future__ import annotations

import argparse
import sys

from .faq import HELP
from .matcher import match


def _first_line(text: str) -> str:
    return text.splitlines()[0] if text else ""


def describe(text: str, pinged: bool) -> str:
    hit = match(text)
    if hit is not None:
        return f"'{text}' -> {hit.entry.id} (score={hit.score})\n{_first_line(hit.entry.answer)}"
    if pinged:
        return f"'{text}' -> ping-with-no-match -> HELP\n{_first_line(HELP)}"
    return f"'{text}' -> no_match"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="faqbot.simulate",
        description="Run the FAQ matcher offline over message text, without connecting to Discord.",
    )
    parser.add_argument(
        "text",
        nargs="*",
        help="message text to match; with none given, one message per line is read from stdin",
    )
    parser.add_argument(
        "-p",
        "--pinged",
        action="store_true",
        help="treat every message as a mention of the account (unmatched text gets HELP)",
    )
    args = parser.parse_args(argv)

    if args.text:
        lines = args.text
    else:
        lines = [line.rstrip("\n") for line in sys.stdin if line.strip()]

    for line in lines:
        print(describe(line, args.pinged))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
