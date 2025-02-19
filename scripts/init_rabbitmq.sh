#!/bin/sh

# Ожидание запуска RabbitMQ
until timeout 1 bash -c "cat < /dev/null > /dev/tcp/${RABBITMQ_HOST}/${RABBITMQ_PORT}"; do
  >&2 echo "RabbitMQ недоступен - ожидание"
  sleep 1
done

# Ожидание готовности management API
until rabbitmqadmin -H ${RABBITMQ_HOST} -P 15672 list queues >/dev/null 2>&1; do
  >&2 echo "Management API недоступен - ожидание"
  sleep 2
done

>&2 echo "RabbitMQ запущен - выполняем инициализацию"

# Создаем пользователя и назначаем права
rabbitmqctl add_user ${RABBITMQ_USER:-polyakov} ${RABBITMQ_PASSWORD:-ewfkIH@UENJkdsc}
rabbitmqctl set_user_tags ${RABBITMQ_USER:-polyakov} administrator
rabbitmqctl set_permissions -p / ${RABBITMQ_USER:-polyakov} ".*" ".*" ".*"

# Создание exchange типа topic
rabbitmqadmin -H ${RABBITMQ_HOST} -P 15672 declare exchange \
    name=${RABBITMQ_EXCHANGE} \
    type=topic \
    durable=true

# Создание очереди
rabbitmqadmin -H ${RABBITMQ_HOST} -P 15672 declare queue \
    name=${RABBITMQ_METRICS_QUEUE} \
    durable=true

# Создание привязки
rabbitmqadmin -H ${RABBITMQ_HOST} -P 15672 declare binding \
    source=${RABBITMQ_EXCHANGE} \
    destination_type=queue \
    destination=${RABBITMQ_METRICS_QUEUE} \
    routing_key=${RABBITMQ_METRICS_ROUTING_KEY}

# Удаляем гостевого пользователя
rabbitmqctl delete_user guest

echo "Инициализация RabbitMQ завершена"