FROM python:3.13

ENV PYTHONUNBUFFERED 1

WORKDIR /usr/app

RUN pip install poetry
COPY ./pyproject.toml ./license.txt ./poetry.lock ./

RUN poetry install --no-root --with dev

COPY . .

RUN useradd admin
RUN chown -R admin:admin ./
USER admin