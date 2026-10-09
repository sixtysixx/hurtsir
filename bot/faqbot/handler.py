from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field

import discord

from .config import Config
from .faq import FOOTER, HELP
from .limits import RateLimiter
from .matcher import match

log = logging.getLogger(__name__)

SEEN_LIMIT = 500
SENT_LIMIT = 500

# The red X users tap to retract an answer that did not help.
VETO_EMOJI = "\u274c"

NO_MENTIONS = discord.AllowedMentions.none()


@dataclass(frozen=True, slots=True)
class SentReply:
    author_id: int
    channel_id: int
    key: str
    message: object


@dataclass(slots=True)
class BotContext:
    config: Config
    limiter: RateLimiter
    seen: deque[int] = field(default_factory=lambda: deque(maxlen=SEEN_LIMIT))
    replied_to: deque[int] = field(default_factory=lambda: deque(maxlen=SEEN_LIMIT))
    # reply message id -> the reply plus who asked for it, so a veto can find it again
    sent: dict[int, SentReply] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class _Reply:
    key: str
    text: str
    score: int | None


def compose_reply(text: str) -> str:
    return f"{text}\n{FOOTER}"


def _decide(message, ctx: BotContext, self_id: int) -> str | _Reply:
    if message.author.id == self_id:
        return "ignored_own"
    if getattr(message.author, "bot", False):
        return "ignored_bot"
    if message.guild is None:
        return "ignored_dm"
    channel_id = message.channel.id
    if ctx.config.allowed_channel_ids and channel_id not in ctx.config.allowed_channel_ids:
        return "ignored_channel"
    if message.id in ctx.seen:
        return "ignored_duplicate"

    reference = message.reference
    addressed = self_id in (message.raw_mentions or []) or (
        reference is not None and reference.message_id in ctx.replied_to
    )

    hit = match(message.content or "")
    if hit is None:
        if not addressed:
            return "no_match"
        reply = _Reply(key="help", text=HELP, score=None)
    else:
        reply = _Reply(key=hit.entry.id, text=hit.entry.answer, score=hit.score)

    if ctx.config.dry_run:
        first_line = reply.text.splitlines()[0] if reply.text else ""
        log.info("dry-run %s -> %s", reply.key, first_line)
        return "dry_run"

    reason = ctx.limiter.check(message.author.id, channel_id, reply.key)
    if reason is not None:
        return reason

    return reply


async def handle_message(message, ctx: BotContext, self_id: int) -> str:
    decision = _decide(message, ctx, self_id)
    if isinstance(decision, str):
        return decision

    answer = await message.reply(compose_reply(decision.text), allowed_mentions=NO_MENTIONS)
    _remember(ctx, answer, message.author.id, message.channel.id, decision.key)
    try:
        await answer.add_reaction(VETO_EMOJI)
    except Exception:
        log.warning("could not add veto reaction to %s", getattr(answer, "id", "?"), exc_info=True)
    ctx.limiter.record(message.author.id, message.channel.id, decision.key)
    ctx.seen.append(message.id)
    if decision.key != "help":
        ctx.replied_to.append(message.id)
    log.info(
        "replied %s in %s (score=%s)",
        decision.key,
        message.channel.id,
        decision.score if decision.score is not None else "-",
    )
    return "replied"


def _remember(
    ctx: BotContext, answer, author_id: int, channel_id: int, key: str
) -> None:
    if answer.id is None:
        return
    ctx.sent[answer.id] = SentReply(
        author_id=author_id, channel_id=channel_id, key=key, message=answer
    )
    while len(ctx.sent) > SENT_LIMIT:
        ctx.sent.pop(next(iter(ctx.sent)))


def _veto_reason(payload, ctx: BotContext, self_id: int) -> str:
    if payload.user_id == self_id:
        # the bot's own red X must never retract the answer it just posted
        return "ignored_self"
    if str(payload.emoji) != VETO_EMOJI:
        return "ignored_emoji"
    record = ctx.sent.get(payload.message_id)
    if record is None:
        return "ignored_unknown"
    if payload.user_id != record.author_id and not _has_csr_role(payload, ctx.config):
        return "ignored_unauthorized"
    return "veto"


def _has_csr_role(payload, config: Config) -> bool:
    if not config.csr_role_ids:
        return False
    member = getattr(payload, "member", None)
    if member is None:
        return False
    return any(role.id in config.csr_role_ids for role in (member.roles or ()))


async def handle_reaction(payload, ctx: BotContext, self_id: int) -> str:
    reason = _veto_reason(payload, ctx, self_id)
    if reason != "veto":
        return reason

    record = ctx.sent.pop(payload.message_id)
    # the reply is gone, so free the slots it held: the asker must be able to retry, and the
    # same question must be answerable again in that channel
    ctx.limiter.release(record.author_id, record.channel_id, record.key)
    try:
        await record.message.delete()
    except discord.NotFound:
        log.info("veto target %s was already gone", payload.message_id)
        return "vetoed_gone"
    log.info("vetoed %s reply %s in %s", record.key, payload.message_id, record.channel_id)
    return "vetoed"
