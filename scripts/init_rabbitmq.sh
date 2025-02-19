#!/bin/sh

# Ожидание запуска RabbitMQ
until timeout 1 bash -c "cat < /dev/null > /dev/tcp/${RABBITMQ_HOST}/${RABBITMQ_PORT}"; do
  >&2 echo "RabbitMQ недоступен - ожидание"
  sleep 1
done

# Ожидание готовности management API
until rabbitmqadmin -H ${RABBITMQ_HOST} -P 15672 -u guest -p guest list queues >/dev/null 2>&1; do
  >&2 echo "Management API недоступен - ожидание"
  sleep 2
done

>&2 echo "RabbitMQ запущен - выполняем инициализацию"

echo "Проверяем переменные окружения:"
echo "RABBITMQ_USER: ${RABBITMQ_USER}"
echo "RABBITMQ_EXCHANGE: ${RABBITMQ_EXCHANGE}"
echo "RABBITMQ_METRICS_QUEUE: ${RABBITMQ_METRICS_QUEUE}"

# Создаем пользователя через management API
echo "Создаем пользователя ${RABBITMQ_USER}..."
rabbitmqadmin -H ${RABBITMQ_HOST} -P 15672 -u guest -p guest declare user \
    name=${RABBITMQ_USER} \
    password=${RABBITMQ_PASSWORD} \
    tags=administrator

# Назначаем права через management API
echo "Назначаем права пользователю ${RABBITMQ_USER}..."
rabbitmqadmin -H ${RABBITMQ_HOST} -P 15672 -u guest -p guest declare permission \
    vhost=/ \
    user=${RABBITMQ_USER} \
    configure=.* \
    write=.* \
    read=.*

# Создание exchange типа topic
echo "Создаем exchange ${RABBITMQ_EXCHANGE}..."
rabbitmqadmin -H ${RABBITMQ_HOST} -P 15672 -u guest -p guest declare exchange \
    name=${RABBITMQ_EXCHANGE} \
    type=topic \
    durable=true

# Создание очереди
echo "Создаем очередь ${RABBITMQ_METRICS_QUEUE}..."
rabbitmqadmin -H ${RABBITMQ_HOST} -P 15672 -u guest -p guest declare queue \
    name=${RABBITMQ_METRICS_QUEUE} \
    durable=true

# Создание привязки
echo "Создаем привязку..."
rabbitmqadmin -H ${RABBITMQ_HOST} -P 15672 -u guest -p guest declare binding \
    source=${RABBITMQ_EXCHANGE} \
    destination_type=queue \
    destination=${RABBITMQ_METRICS_QUEUE} \
    routing_key=${RABBITMQ_METRICS_ROUTING_KEY}

# Проверяем созданного пользователя
echo "Проверяем созданного пользователя и его права:"
rabbitmqadmin -H ${RABBITMQ_HOST} -P 15672 -u guest -p guest list users
rabbitmqadmin -H ${RABBITMQ_HOST} -P 15672 -u guest -p guest list permissions

# Удаляем гостевого пользователя через management API только после успешного создания нового
if rabbitmqadmin -H ${RABBITMQ_HOST} -P 15672 -u ${RABBITMQ_USER} -p ${RABBITMQ_PASSWORD} list users >/dev/null 2>&1; then
    echo "Новый пользователь работает, удаляем guest..."
    rabbitmqadmin -H ${RABBITMQ_HOST} -P 15672 -u ${RABBITMQ_USER} -p ${RABBITMQ_PASSWORD} delete user name=guest || true
else
    echo "ОШИБКА: Не удалось подтвердить работу нового пользователя, оставляем guest"
fi

echo "Финальный список пользователей:"
rabbitmqadmin -H ${RABBITMQ_HOST} -P 15672 -u ${RABBITMQ_USER} -p ${RABBITMQ_PASSWORD} list users

echo "Инициализация RabbitMQ завершена"