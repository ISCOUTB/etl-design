FROM python:3.13-alpine

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONPATH=.

COPY packages/autoscaler/ /app/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync

CMD [ "uv", "run", "-m", "src.main" ]