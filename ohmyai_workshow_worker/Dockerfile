FROM python:3.12-alpine

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /var/log \
    && touch /var/log/worker.log

# Создаем cron файл
RUN echo "0 * * * * /usr/local/bin/python /app/worker.py >> /var/log/worker.log 2>&1" > /app/mycron \
    && crontab /app/mycron

CMD crond -f && tail -f /var/log/worker.log 