FROM python:3.12-alpine

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt 

COPY . .

# Устанавливаем cron задачу из файла
RUN crontab mycron

CMD ["crond", "-f", "-l", "8"]
