FROM python:3.13

ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/root/.local/bin:$PATH"

WORKDIR /usr/app

RUN pip install --no-cache-dir poetry
COPY ./pyproject.toml ./poetry.lock ./license.txt ./
RUN poetry install --no-root --with dev

COPY . .

RUN useradd -m admin && chown -R admin:admin /usr/app
USER admin