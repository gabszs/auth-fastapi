FROM python:3.13-alpine as builder

RUN pip install poetry==2.1.3

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR app/

COPY pyproject.toml poetry.lock ./

#RUN touch README.md

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --without dev --no-root
ENV PATH="/app/.venv/bin:$PATH"
# Nota: opentelemetry-bootstrap geralmente baixa pacotes.
RUN opentelemetry-bootstrap -a install

FROM python:3.13-alpine as runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY app ./app
COPY pyproject.toml poetry.lock ./
COPY migrations ./migrations
COPY alembic.ini ./

EXPOSE 80

CMD [ "sh", "-c", "alembic upgrade head && opentelemetry-instrument uvicorn --proxy-headers --host 0.0.0.0 --port 80 app.main:app"]
# CMD ["opentelemetry-instrument", "uvicorn", "--host", "0.0.0.0", "--port", "80", "app.main:app"]
