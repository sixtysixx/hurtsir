from __future__ import annotations

import logging
import sys

import discord
from dotenv import load_dotenv

from .client import build_client
from .config import load_config

log = logging.getLogger(__name__)


def main() -> int:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    config = load_config()
    if config.dry_run:
        log.warning("FAQ_DRY_RUN is on - matching and logging only, nothing will be sent")
    client = build_client(config)
    try:
        client.run(config.token)
    except discord.LoginFailure as exc:
        print(f"Discord rejected the login: {exc}", file=sys.stderr)
        return 1
    except discord.CaptchaRequired:
        print(
            "Discord wants a CAPTCHA for this login. Sign into the account once from this "
            "machine/IP with the normal client, then retry.",
            file=sys.stderr,
        )
        return 1
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
