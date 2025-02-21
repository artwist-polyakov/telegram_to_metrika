FROM python:3.12-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt .

RUN apk update \
    && apk add --no-cache build-base \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && apk add --no-cache dcron

COPY . .

# Создаем директорию для логов
RUN mkdir -p /var/log \
    && touch /var/log/cron.log \
    && chmod 0644 /var/log/cron.log

# Добавляем задачу в cron
RUN echo "0 * * * * /usr/local/bin/python /app/cron_runner.py >> /var/log/cron.log 2>&1" > /etc/crontabs/root \
    && chmod 0644 /etc/crontabs/root

ENV PYTHONPATH=/app

# Создаем скрипт для запуска
RUN echo '#!/bin/sh' > /entrypoint.sh \
    && echo 'crond -f -d 8' >> /entrypoint.sh \
    && chmod +x /entrypoint.sh

# Запускаем cron через entrypoint
ENTRYPOINT ["/entrypoint.sh"] 