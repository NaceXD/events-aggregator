FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv/bin/

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PATH="/uv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY src/ ./src/
COPY run.sh ./
COPY alembic.ini ./
COPY migrations/ ./migrations/

RUN chmod +x run.sh

EXPOSE 8000

CMD ["bash", "./run.sh"]
