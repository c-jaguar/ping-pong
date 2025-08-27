FROM python:3.10-slim-bookworm AS build

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  # Poetry's configuration:
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  POETRY_HOME='/usr/local' \
  POETRY_VERSION=2.1.3
  # ^^^
  # Make sure to update it!


# Copy only requirements to cache them in docker layer
WORKDIR /app
COPY poetry.lock pyproject.toml /app/



# Project initialization:
RUN apt-get update && \
  apt-get install -y curl && \
  curl -sSL https://install.python-poetry.org | python3 -

FROM build AS dev

# Creating folders, and files for a project:
COPY . /app
RUN poetry install --only main --no-interaction --no-ansi --no-root && \
    touch log.txt

FROM dev AS runtime

ENV APPLICATION_TYPE=${APPLICATION_TYPE}
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh
ENTRYPOINT exec ./docker-entrypoint.sh $APPLICATION_TYPE
