FROM python:3.10
LABEL maintainer="Felipe Bogaerts de Mattos"

ENV PYTHONUNBUFFERED 1

WORKDIR /usr/app

COPY ./requirements.txt ./requirements.txt
RUN pip3 install -r ./requirements.txt

COPY . .

RUN chmod +x ./scripts/*

RUN useradd admin
RUN chown -R admin:admin ./
USER admin

EXPOSE 8000

ENTRYPOINT ["sh", "./scripts/entrypoint.sh"]