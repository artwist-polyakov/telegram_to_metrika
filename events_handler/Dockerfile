FROM python:3.12-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt .

RUN apk update \
    && apk add --no-cache build-base \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

RUN chmod +x /app/events_handler/entrypoint.sh

CMD ["/bin/sh", "/app/events_handler/entrypoint.sh"]