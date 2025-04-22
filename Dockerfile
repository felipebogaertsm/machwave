FROM python:3.13-slim-bullseye

ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/root/.local/bin:$PATH"

WORKDIR /usr/app

# Install system build dependencies for rocketcea (Meson + Fortran)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      gfortran \
      ninja-build \
      pkg-config \
      python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Install project dependencies (including dev) without creating a venv
COPY pyproject.toml poetry.lock license.txt ./
RUN poetry install --no-root --with dev

# Copy in the rest of the source
COPY . .

# Create non-root user and drop privileges
RUN useradd -m admin && chown -R admin:admin /usr/app
USER admin
