FROM python:3.12-bookworm AS builder
ARG PYPI_MIRROR
RUN if [ -n "$PYPI_MIRROR" ]; then \
    # Configure pip
    pip config set global.index-url "$PYPI_MIRROR" && \
    # Install poetry
    pip install poetry==2.1.1 poetry-plugin-pypi-mirror==0.6.1 && \
    # Configure poetry using the plugin
    mkdir -p /root/.config/pypoetry && \
    echo '[plugins.pypi_mirror]' > /root/.config/pypoetry/config.toml && \
    echo "url = \"$PYPI_MIRROR\"" >> /root/.config/pypoetry/config.toml; \
    else \
    # No mirror, install poetry directly
    pip install poetry==2.1.1; \
    fi
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache
WORKDIR /app-src
COPY ./pyproject.toml ./poetry.lock ./
RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry sync --no-root
COPY ./README.md ./LICENSE.md ./
COPY ./src ./src
RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry sync

FROM python:3.12-slim-bookworm AS runtime
ENV TZ=Asia/Shanghai \
    VIRTUAL_ENV=/app-src/.venv \
    PATH="/app-src/.venv/bin:$PATH"
COPY --from=builder /app-src /app-src
RUN mkdir -p /app
WORKDIR /app
ENTRYPOINT ["python", "-m", "njupt_smartclass_downloader"]
