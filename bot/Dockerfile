FROM ghcr.io/astral-sh/uv:0.11.7-python3.13-trixie-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --locked

COPY faqbot ./faqbot

RUN useradd --create-home --uid 10001 bot && chown -R bot:bot /app
USER bot
ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "-m", "faqbot"]
