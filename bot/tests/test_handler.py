from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from types import SimpleNamespace

import discord

from faqbot.config import Config
from faqbot.faq import FOOTER
from faqbot.handler import (
    SENT_LIMIT,
    VETO_EMOJI,
    BotContext,
    handle_message,
    handle_reaction,
)
from faqbot.limits import RateLimiter

SELF_ID = 999


class Clock:
    def __init__(self) -> None:
        self.value = 1000.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


@dataclass
class Author:
    id: int
    bot: bool = False


@dataclass
class Channel:
    id: int


@dataclass
class Reference:
    message_id: int


@dataclass
class Role:
    id: int


@dataclass
class Member:
    roles: list[Role]


@dataclass
class SentMessage:
    id: int
    text: str
    mentions: object
    reactions: list[str] = field(default_factory=list)
    deleted: bool = False
    delete_error: Exception | None = None

    async def add_reaction(self, emoji: str) -> None:
        self.reactions.append(emoji)

    async def delete(self) -> None:
        if self.delete_error is not None:
            raise self.delete_error
        self.deleted = True


@dataclass
class Message:
    id: int
    content: str
    channel: Channel
    guild: object | None = object()
    author: Author = field(default_factory=lambda: Author(id=1))
    raw_mentions: list[int] = field(default_factory=list)
    reference: Reference | None = None
    replies: list[SentMessage] = field(default_factory=list)
    reply_error: Exception | None = None
    reaction_error: Exception | None = None

    async def reply(self, text: str, **kwargs) -> SentMessage:
        if self.reply_error is not None:
            raise self.reply_error
        sent = SentMessage(
            id=self.id * 1000 + 1, text=text, mentions=kwargs.get("allowed_mentions")
        )
        if self.reaction_error is not None:
            sent.delete_error = None
        self.replies.append(sent)
        if self.reaction_error is not None:
            async def _boom(_emoji: str) -> None:
                raise self.reaction_error  # type: ignore[misc]

            sent.add_reaction = _boom  # type: ignore[method-assign]
        return sent


@dataclass
class Payload:
    user_id: int
    message_id: int
    channel_id: int = 10
    emoji: str = VETO_EMOJI
    member: Member | None = None


def _config(**overrides) -> Config:
    base = {
        "token": "x",
        "allowed_channel_ids": frozenset(),
        "csr_role_ids": frozenset(),
        "dry_run": False,
        "user_cooldown_s": 15.0,
        "channel_cooldown_s": 5.0,
        "max_replies_per_minute": 10,
        "duplicate_window_s": 60.0,
    }
    return Config(**{**base, **overrides})


def _context(clock: Clock | None = None, **overrides) -> BotContext:
    config = _config(**overrides)
    return BotContext(config=config, limiter=RateLimiter.from_config(config, now=clock or Clock()))


def _run(message: Message, ctx: BotContext, self_id: int = SELF_ID) -> str:
    return asyncio.run(handle_message(message, ctx, self_id))


def _react(payload: Payload, ctx: BotContext, self_id: int = SELF_ID) -> str:
    return asyncio.run(handle_reaction(payload, ctx, self_id))


# --- message guards ---------------------------------------------------------------


def test_ignores_own_message() -> None:
    message = Message(id=1, content="inject failed", channel=Channel(10), author=Author(SELF_ID))
    assert _run(message, _context()) == "ignored_own"
    assert message.replies == []


def test_ignores_bot_message() -> None:
    message = Message(id=1, content="inject failed", channel=Channel(10), author=Author(2, bot=True))
    assert _run(message, _context()) == "ignored_bot"


def test_ignores_dm() -> None:
    message = Message(id=1, content="inject failed", channel=Channel(10), guild=None)
    assert _run(message, _context()) == "ignored_dm"


def test_ignores_channel_not_allowed() -> None:
    message = Message(id=1, content="inject failed", channel=Channel(10))
    assert _run(message, _context(allowed_channel_ids=frozenset({20}))) == "ignored_channel"


def test_allows_listed_channel() -> None:
    message = Message(id=1, content="inject failed", channel=Channel(20))
    assert _run(message, _context(allowed_channel_ids=frozenset({20}))) == "replied"


def test_ignores_duplicate_message_id() -> None:
    ctx = _context()
    first = Message(id=7, content="inject failed", channel=Channel(10))
    assert _run(first, ctx) == "replied"
    second = Message(id=7, content="inject failed", channel=Channel(10))
    assert _run(second, ctx) == "ignored_duplicate"
    assert second.replies == []


def test_no_match_without_ping_sends_nothing() -> None:
    message = Message(id=1, content="hello there", channel=Channel(10))
    assert _run(message, _context()) == "no_match"
    assert message.replies == []


# --- replies ----------------------------------------------------------------------


def test_ping_without_topic_gets_help() -> None:
    message = Message(
        id=1, content="<@999> hello there", channel=Channel(10), raw_mentions=[SELF_ID]
    )
    assert _run(message, _context()) == "replied"
    assert len(message.replies) == 1
    assert message.replies[0].text.startswith("**SirHurt FAQ**")
    assert "#support" in message.replies[0].text


def test_keyword_without_ping_gets_entry_answer() -> None:
    message = Message(id=1, content="inject failed", channel=Channel(10))
    assert _run(message, _context()) == "replied"
    answer = message.replies[0]
    assert "Injection checklist" in answer.text
    assert "https://sirhurt.pages.dev/guide/injection/" in answer.text


def test_every_reply_carries_the_footer() -> None:
    ctx = _context()
    texts = ["inject failed", "am i banned", "where is my key"]
    for index, text in enumerate(texts, start=1):
        # distinct channel per message: a shared one would trip the channel cooldown
        message = Message(
            id=index, content=text, channel=Channel(100 + index), author=Author(id=index)
        )
        assert _run(message, ctx) == "replied"
        assert message.replies[0].text.endswith(FOOTER)
        assert "automated reply" in message.replies[0].text


def test_help_reply_carries_the_footer() -> None:
    ctx = _context()
    message = Message(id=1, content="<@999> hi", channel=Channel(10), raw_mentions=[SELF_ID])
    assert _run(message, ctx) == "replied"
    assert message.replies[0].text.endswith(FOOTER)


def test_help_reply_does_not_mark_thread_followup() -> None:
    ctx = _context()
    ping = Message(id=1, content="<@999> hello", channel=Channel(10), raw_mentions=[SELF_ID])
    assert _run(ping, ctx) == "replied"
    assert list(ctx.replied_to) == []
    assert list(ctx.seen) == [1]


def test_reply_to_a_replied_message_is_addressed() -> None:
    clock = Clock()
    ctx = _context(clock=clock)
    first = Message(id=11, content="inject failed", channel=Channel(20))
    assert _run(first, ctx) == "replied"
    assert list(ctx.replied_to) == [11]

    clock.advance(120)
    follow_up = Message(
        id=12,
        content="still nothing here",
        channel=Channel(20),
        reference=Reference(message_id=11),
    )
    assert _run(follow_up, ctx) == "replied"
    assert follow_up.replies[0].text.startswith("**SirHurt FAQ**")


def test_reply_to_an_unrelated_message_is_not_addressed() -> None:
    ctx = _context()
    message = Message(
        id=12,
        content="still nothing here",
        channel=Channel(20),
        reference=Reference(message_id=11),
    )
    assert _run(message, ctx) == "no_match"
    assert message.replies == []


def test_reply_suppresses_all_mentions() -> None:
    message = Message(id=1, content="inject failed", channel=Channel(10))
    assert _run(message, _context()) == "replied"
    mentions = message.replies[0].mentions
    assert mentions.everyone is False
    assert mentions.users is False
    assert mentions.roles is False


# --- dry run and limits -----------------------------------------------------------


def test_dry_run_sends_nothing() -> None:
    ctx = _context(dry_run=True)
    message = Message(id=1, content="inject failed", channel=Channel(10))
    assert _run(message, ctx) == "dry_run"
    assert message.replies == []
    assert list(ctx.seen) == []
    assert ctx.sent == {}


def test_dry_run_does_not_consume_cooldown() -> None:
    ctx = _context(dry_run=True)
    first = Message(id=1, content="inject failed", channel=Channel(10))
    second = Message(id=2, content="inject failed", channel=Channel(10))
    assert _run(first, ctx) == "dry_run"
    assert _run(second, ctx) == "dry_run"


def test_second_message_from_same_user_is_cooled_down() -> None:
    ctx = _context()
    first = Message(id=1, content="inject failed", channel=Channel(10))
    second = Message(id=2, content="antivirus deleted my files", channel=Channel(10))
    assert _run(first, ctx) == "replied"
    assert _run(second, ctx) == "cooldown_user"
    assert second.replies == []


def test_channel_cooldown_hits_another_user() -> None:
    ctx = _context()
    first = Message(id=1, content="inject failed", channel=Channel(10))
    second = Message(
        id=2, content="antivirus deleted my files", channel=Channel(10), author=Author(id=2)
    )
    assert _run(first, ctx) == "replied"
    assert _run(second, ctx) == "cooldown_channel"


def test_duplicate_answer_in_one_channel_is_suppressed() -> None:
    clock = Clock()
    ctx = _context(clock=clock)
    first = Message(id=1, content="inject failed", channel=Channel(10))
    assert _run(first, ctx) == "replied"
    clock.advance(30)
    second = Message(id=2, content="inject failed", channel=Channel(10), author=Author(id=2))
    assert _run(second, ctx) == "cooldown_duplicate"


def test_seen_and_replied_to_are_bounded() -> None:
    ctx = _context()
    assert ctx.seen.maxlen == 500
    assert ctx.replied_to.maxlen == 500


# --- veto reaction ----------------------------------------------------------------


def test_reply_gets_the_veto_reaction() -> None:
    message = Message(id=1, content="inject failed", channel=Channel(10))
    assert _run(message, _context()) == "replied"
    assert message.replies[0].reactions == [VETO_EMOJI]


def test_reply_reaction_failure_does_not_fail_handling() -> None:
    ctx = _context()
    message = Message(
        id=1,
        content="inject failed",
        channel=Channel(10),
        reaction_error=RuntimeError("no permission"),
    )
    assert _run(message, ctx) == "replied"
    assert list(ctx.seen) == [1]


def test_reply_is_tracked_for_veto() -> None:
    ctx = _context()
    message = Message(id=5, content="inject failed", channel=Channel(10), author=Author(id=42))
    assert _run(message, ctx) == "replied"
    assert ctx.sent[message.replies[0].id].author_id == 42


def test_untracked_reply_without_id_is_skipped() -> None:
    ctx = _context()

    class NoId(Message):
        async def reply(self, text: str, **kwargs) -> SentMessage:
            self.replies.append(SentMessage(id=None, text=text, mentions=None))  # type: ignore[arg-type]
            return self.replies[-1]

    message = NoId(id=1, content="inject failed", channel=Channel(10))
    assert _run(message, ctx) == "replied"
    assert ctx.sent == {}


def test_sent_map_is_bounded() -> None:
    # this asserts the tracking map's bound, so the per-minute cap is taken out of the way
    ctx = _context(max_replies_per_minute=SENT_LIMIT * 2)
    for index in range(SENT_LIMIT + 20):
        message = Message(
            id=index,
            content="inject failed",
            channel=Channel(1000 + index),
            author=Author(id=index),
        )
        assert _run(message, ctx) == "replied"
    assert len(ctx.sent) == SENT_LIMIT


def test_self_reaction_never_retracts() -> None:
    ctx = _context()
    message = Message(id=1, content="inject failed", channel=Channel(10))
    assert _run(message, ctx) == "replied"
    answer = message.replies[0]
    assert _react(Payload(user_id=SELF_ID, message_id=answer.id), ctx) == "ignored_self"
    assert answer.deleted is False


def test_own_reaction_is_ignored_even_when_the_account_is_staff() -> None:
    """The account running the bot often *has* a staff role. Its own auto-reaction must never
    retract the answer - without the self guard this deletes every reply on arrival."""
    ctx = _context(csr_role_ids=frozenset({500}))
    message = Message(id=1, content="inject failed", channel=Channel(10), author=Author(id=42))
    assert _run(message, ctx) == "replied"
    answer = message.replies[0]
    payload = Payload(user_id=SELF_ID, message_id=answer.id, member=Member(roles=[Role(500)]))
    assert _react(payload, ctx) == "ignored_self"
    assert answer.deleted is False
    assert answer.id in ctx.sent


def test_only_the_veto_emoji_retracts() -> None:
    ctx = _context()
    message = Message(id=1, content="inject failed", channel=Channel(10))
    assert _run(message, ctx) == "replied"
    answer = message.replies[0]
    for emoji in ("\U0001f44d", "\u2705", "\u274e", "\u2716\ufe0f"):
        assert _react(Payload(user_id=1, message_id=answer.id, emoji=emoji), ctx) == "ignored_emoji"
    assert answer.deleted is False


# --- retraction must not lock the channel out -------------------------------------


def test_retry_right_after_a_veto_is_answered() -> None:
    """Reported bug: after a veto the asker got no further replies. The deleted reply must not
    keep its cooldown slots, or retracting a wrong answer would prevent the corrected one."""
    ctx = _context()
    first = Message(id=1, content="inject failed", channel=Channel(10), author=Author(id=42))
    assert _run(first, ctx) == "replied"
    assert _react(Payload(user_id=42, message_id=first.replies[0].id), ctx) == "vetoed"

    retry = Message(id=2, content="inject failed", channel=Channel(10), author=Author(id=42))
    assert _run(retry, ctx) == "replied"
    assert len(retry.replies) == 1


def test_veto_frees_the_question_for_other_users() -> None:
    ctx = _context()
    first = Message(id=1, content="inject failed", channel=Channel(10), author=Author(id=42))
    assert _run(first, ctx) == "replied"
    assert _react(Payload(user_id=42, message_id=first.replies[0].id), ctx) == "vetoed"

    other = Message(id=2, content="inject failed", channel=Channel(10), author=Author(id=43))
    assert _run(other, ctx) == "replied"


def test_csr_veto_frees_the_channel_for_the_asker() -> None:
    ctx = _context(csr_role_ids=frozenset({500}))
    first = Message(id=1, content="inject failed", channel=Channel(10), author=Author(id=42))
    assert _run(first, ctx) == "replied"
    staff = Payload(
        user_id=7, message_id=first.replies[0].id, member=Member(roles=[Role(500)])
    )
    assert _react(staff, ctx) == "vetoed"

    retry = Message(id=2, content="where is my key", channel=Channel(10), author=Author(id=42))
    assert _run(retry, ctx) == "replied"


def test_veto_does_not_refund_the_global_budget() -> None:
    """Ask/veto cycles must still be capped by the per-minute volume limit."""
    ctx = _context(max_replies_per_minute=3)
    results = []
    for index in range(4):
        message = Message(
            id=100 + index,
            content="inject failed",
            channel=Channel(50 + index),
            author=Author(id=200 + index),
        )
        outcome = _run(message, ctx)
        results.append(outcome)
        if outcome == "replied":
            payload = Payload(user_id=200 + index, message_id=message.replies[0].id)
            assert _react(payload, ctx) == "vetoed"
    assert results == ["replied", "replied", "replied", "cooldown_global"]


def test_veto_only_clears_the_retracted_reply() -> None:
    ctx = _context()
    first = Message(id=1, content="inject failed", channel=Channel(10), author=Author(id=42))
    second = Message(id=2, content="where is my key", channel=Channel(11), author=Author(id=43))
    assert _run(first, ctx) == "replied"
    assert _run(second, ctx) == "replied"

    assert _react(Payload(user_id=42, message_id=first.replies[0].id), ctx) == "vetoed"

    # the untouched reply's channel is still protected
    later = Message(id=3, content="am i banned", channel=Channel(11), author=Author(id=44))
    assert _run(later, ctx) == "cooldown_channel"


def test_veto_releases_even_when_the_message_was_already_gone() -> None:
    ctx = _context()
    message = Message(id=1, content="inject failed", channel=Channel(10), author=Author(id=42))
    assert _run(message, ctx) == "replied"
    answer = message.replies[0]
    answer.delete_error = discord.NotFound(
        SimpleNamespace(status=404, reason="Not Found"), "Unknown Message"
    )
    assert _react(Payload(user_id=42, message_id=answer.id), ctx) == "vetoed_gone"

    retry = Message(id=2, content="inject failed", channel=Channel(10), author=Author(id=42))
    assert _run(retry, ctx) == "replied"


def test_author_can_retract_their_answer() -> None:
    ctx = _context()
    message = Message(id=1, content="inject failed", channel=Channel(10), author=Author(id=42))
    assert _run(message, ctx) == "replied"
    answer = message.replies[0]
    assert _react(Payload(user_id=42, message_id=answer.id), ctx) == "vetoed"
    assert answer.deleted is True
    assert answer.id not in ctx.sent


def test_reaction_on_an_unknown_message_is_ignored() -> None:
    ctx = _context()
    assert _react(Payload(user_id=42, message_id=12345), ctx) == "ignored_unknown"


def test_other_users_cannot_retract() -> None:
    ctx = _context()
    message = Message(id=1, content="inject failed", channel=Channel(10), author=Author(id=42))
    assert _run(message, ctx) == "replied"
    answer = message.replies[0]
    payload = Payload(user_id=7, message_id=answer.id, member=Member(roles=[Role(500)]))
    assert _react(payload, ctx) == "ignored_unauthorized"
    assert answer.deleted is False
    assert answer.id in ctx.sent


def test_csr_role_can_retract() -> None:
    ctx = _context(csr_role_ids=frozenset({500}))
    message = Message(id=1, content="inject failed", channel=Channel(10), author=Author(id=42))
    assert _run(message, ctx) == "replied"
    answer = message.replies[0]
    payload = Payload(user_id=7, message_id=answer.id, member=Member(roles=[Role(1), Role(500)]))
    assert _react(payload, ctx) == "vetoed"
    assert answer.deleted is True


def test_csr_role_outside_the_list_cannot_retract() -> None:
    ctx = _context(csr_role_ids=frozenset({500}))
    message = Message(id=1, content="inject failed", channel=Channel(10), author=Author(id=42))
    assert _run(message, ctx) == "replied"
    answer = message.replies[0]
    payload = Payload(user_id=7, message_id=answer.id, member=Member(roles=[Role(501)]))
    assert _react(payload, ctx) == "ignored_unauthorized"


def test_memberless_reaction_from_a_stranger_cannot_retract() -> None:
    ctx = _context(csr_role_ids=frozenset({500}))
    message = Message(id=1, content="inject failed", channel=Channel(10), author=Author(id=42))
    assert _run(message, ctx) == "replied"
    answer = message.replies[0]
    assert _react(Payload(user_id=7, message_id=answer.id), ctx) == "ignored_unauthorized"


def test_second_veto_on_the_same_reply_is_ignored() -> None:
    ctx = _context()
    message = Message(id=1, content="inject failed", channel=Channel(10), author=Author(id=42))
    assert _run(message, ctx) == "replied"
    answer = message.replies[0]
    assert _react(Payload(user_id=42, message_id=answer.id), ctx) == "vetoed"
    assert _react(Payload(user_id=42, message_id=answer.id), ctx) == "ignored_unknown"


def test_veto_tolerates_an_already_deleted_message() -> None:
    ctx = _context()
    message = Message(id=1, content="inject failed", channel=Channel(10), author=Author(id=42))
    assert _run(message, ctx) == "replied"
    answer = message.replies[0]
    answer.delete_error = discord.NotFound(
        SimpleNamespace(status=404, reason="Not Found"), "Unknown Message"
    )
    assert _react(Payload(user_id=42, message_id=answer.id), ctx) == "vetoed_gone"
    assert answer.id not in ctx.sent


def test_each_reply_is_vetoed_by_its_own_author() -> None:
    ctx = _context()
    first = Message(id=1, content="inject failed", channel=Channel(10), author=Author(id=42))
    second = Message(id=2, content="where is my key", channel=Channel(11), author=Author(id=43))
    assert _run(first, ctx) == "replied"
    assert _run(second, ctx) == "replied"

    first_answer, second_answer = first.replies[0], second.replies[0]
    # the asker of the first reply must not retract the second
    assert _react(Payload(user_id=42, message_id=second_answer.id), ctx) == "ignored_unauthorized"
    assert second_answer.deleted is False
    assert _react(Payload(user_id=42, message_id=first_answer.id), ctx) == "vetoed"
    assert first_answer.deleted is True
    assert second_answer.deleted is False
