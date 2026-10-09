from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass, field

from faqbot.client import build_client
from faqbot.config import Config
from faqbot.faq import FOOTER
from faqbot.handler import VETO_EMOJI


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


@dataclass
class Sent:
    id: int
    text: str
    reactions: list[str] = field(default_factory=list)
    deleted: bool = False

    async def add_reaction(self, emoji: str) -> None:
        self.reactions.append(emoji)

    async def delete(self) -> None:
        self.deleted = True


@dataclass
class _Peer:
    id: int
    bot: bool = False


@dataclass
class StubMessage:
    id: int
    content: str
    channel: object
    guild: object | None
    author: _Peer
    raw_mentions: list[int] = field(default_factory=list)
    reference: object | None = None
    sent: list[Sent] = field(default_factory=list)

    async def reply(self, text: str, **kwargs) -> Sent:
        answer = Sent(id=self.id * 1000 + 1, text=text)
        self.sent.append(answer)
        return answer


@dataclass
class StubPayload:
    user_id: int
    message_id: int
    channel_id: int = 77
    emoji: str = VETO_EMOJI
    member: object | None = None


def _ready(client, self_id: int = 1) -> None:
    class _User:
        id = self_id

    _User.__str__ = lambda _self: "bot#0001"  # type: ignore[method-assign]
    client._connection.user = _User()


def _stub(message_id: int = 1, content: str = "inject failed", author_id: int = 42) -> StubMessage:
    return StubMessage(
        id=message_id,
        content=content,
        channel=_Peer(10),
        guild=object(),
        author=_Peer(author_id),
    )


def test_build_client_registers_every_handler() -> None:
    """Guards the wiring itself: nothing else imports this module, so a broken import or a
    dropped event registration would only show up against live Discord."""
    client = build_client(_config())
    for name in ("on_ready", "on_message", "on_raw_reaction_add"):
        handler = getattr(client, name, None)
        assert handler is not None, f"{name} was not registered"
        assert inspect.iscoroutinefunction(handler), f"{name} is not a coroutine function"


def test_message_before_ready_is_ignored() -> None:
    client = build_client(_config())
    message = _stub()

    async def main() -> None:
        client.loop = asyncio.get_running_loop()
        client.dispatch("message", message)
        await asyncio.sleep(0.05)

    asyncio.run(main())
    assert message.sent == []


def test_dispatched_message_replies_with_footer_and_veto_reaction() -> None:
    client = build_client(_config())
    _ready(client)
    message = _stub()

    async def main() -> None:
        client.loop = asyncio.get_running_loop()
        client.dispatch("message", message)
        await asyncio.sleep(0.05)

    asyncio.run(main())
    assert len(message.sent) == 1
    assert message.sent[0].text.endswith(FOOTER)
    assert message.sent[0].reactions == [VETO_EMOJI]


def test_dispatched_veto_by_the_asker_deletes_the_reply() -> None:
    client = build_client(_config())
    _ready(client)
    message = _stub()

    async def main() -> None:
        client.loop = asyncio.get_running_loop()
        client.dispatch("message", message)
        await asyncio.sleep(0.05)
        answer = message.sent[0]

        # the bot's own red X must not retract the answer it just posted
        client.dispatch("raw_reaction_add", StubPayload(user_id=1, message_id=answer.id))
        await asyncio.sleep(0.05)
        assert answer.deleted is False

        client.dispatch("raw_reaction_add", StubPayload(user_id=42, message_id=answer.id))
        await asyncio.sleep(0.05)
        assert answer.deleted is True

    asyncio.run(main())


def test_dispatched_veto_by_csr_role_deletes_the_reply() -> None:
    client = build_client(_config(csr_role_ids=frozenset({500})))
    _ready(client)
    message = _stub(content="where is my key")
    member = type("M", (), {"roles": [type("R", (), {"id": 500})()]})()

    async def main() -> None:
        client.loop = asyncio.get_running_loop()
        client.dispatch("message", message)
        await asyncio.sleep(0.05)
        answer = message.sent[0]
        client.dispatch(
            "raw_reaction_add", StubPayload(user_id=8, message_id=answer.id, member=member)
        )
        await asyncio.sleep(0.05)
        assert answer.deleted is True

    asyncio.run(main())
