#!/bin/sh

# Ожидание запуска RabbitMQ
set -e
until timeout 1 bash -c "cat < /dev/null > /dev/tcp/${RABBITMQ_HOST}/${RABBITMQ_PORT}"; do
  >&2 echo "RabbitMQ недоступен - ожидание"
  sleep 1
done

>&2 echo "RabbitMQ запущен - выполняем инициализацию"

# Создание exchange
rabbitmqadmin -H ${RABBITMQ_HOST} declare exchange \
    name=${RABBITMQ_EXCHANGE} \
    type=topic \
    durable=true

# Создание очереди
rabbitmqadmin -H ${RABBITMQ_HOST} declare queue \
    name=${RABBITMQ_METRICS_QUEUE} \
    durable=true

# Создание привязки
rabbitmqadmin -H ${RABBITMQ_HOST} declare binding \
    source=${RABBITMQ_EXCHANGE} \
    destination_type=queue \
    destination=${RABBITMQ_METRICS_QUEUE} \
    routing_key=${RABBITMQ_METRICS_ROUTING_KEY}

# Создание пользователя
rabbitmqadmin -H ${RABBITMQ_HOST} declare user \
    name=${RABBITMQ_USER} \
    password=${RABBITMQ_PASSWORD} \
    tags=administrator

# Назначение прав
rabbitmqadmin -H ${RABBITMQ_HOST} declare permission \
    vhost=/ \
    user=${RABBITMQ_USER} \
    configure=.* \
    write=.* \
    read=.*

echo "Инициализация завершена"
