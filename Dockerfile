FROM python:3.9-slim-buster

RUN pip3 install gunicorn

WORKDIR /app

COPY src /app/src

COPY pyproject.toml .
COPY poetry.lock .
RUN pip3 install .

COPY migrations /app/migrations
COPY wsgi.py .
COPY Procfile .
COPY CHECKS .
