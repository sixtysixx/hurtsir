from __future__ import annotations

import logging

import discord

from .config import Config
from .handler import BotContext, handle_message, handle_reaction
from .limits import RateLimiter

log = logging.getLogger(__name__)


def build_client(config: Config) -> discord.Client:
    client = discord.Client()
    ctx = BotContext(config=config, limiter=RateLimiter.from_config(config))

    @client.event
    async def on_ready() -> None:
        log.info("logged in as %s (%s)", client.user, client.user.id)

    @client.event
    async def on_message(message: discord.Message) -> None:
        if client.user is None:
            return
        try:
            await handle_message(message, ctx, client.user.id)
        except Exception:
            log.exception("failed handling message %s", getattr(message, "id", "?"))

    @client.event
    async def on_raw_reaction_add(payload: discord.RawReactionActionEvent) -> None:
        if client.user is None:
            return
        try:
            await handle_reaction(payload, ctx, client.user.id)
        except Exception:
            log.exception("failed handling reaction on message %s", payload.message_id)

    return client
