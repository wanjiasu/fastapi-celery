FROM python:3.11-slim

WORKDIR /app

# psycopg2 需要一些依赖（slim 下常见）
RUN apt-get update && apt-get install -y --no-install-recommends -o Acquire::Retries=3 --fix-missing \
    curl \
    gcc \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

RUN uv venv
ENV VIRTUAL_ENV="/app/.venv"
ENV PATH="/app/.venv/bin:${PATH}"

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

# 默认不启动，交给 docker-compose 里的 command
