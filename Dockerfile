FROM python:3.9-slim-buster

RUN apt-get update && \
    apt-get install --no-install-recommends -y uwsgi &&\
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY src /app/src

COPY pyproject.toml .
COPY poetry.lock .
RUN pip3 install .

COPY migrations /app/migrations
COPY wsgi.py .
COPY Procfile .
COPY CHECKS .
