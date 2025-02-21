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

# Добавляем задачу в cron
RUN echo "0 * * * * /usr/local/bin/python /app/cron_runner.py >> /var/log/cron.log 2>&1" > /etc/crontabs/root

ENV PYTHONPATH=/app

# Запускаем cron в фоновом режиме
CMD ["crond", "-f", "-d", "8"] 