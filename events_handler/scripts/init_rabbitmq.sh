#!/bin/bash

# Ждем, пока RabbitMQ запустится
until rabbitmqctl node_health_check; do
    echo "Waiting for RabbitMQ to start..."
    sleep 2
done

# Создаем exchange
rabbitmqadmin declare exchange name=$RABBITMQ_EXCHANGE type=topic durable=true

# Создаем очередь
rabbitmqadmin declare queue name=$RABBITMQ_METRICS_QUEUE durable=true

# Создаем привязку
rabbitmqadmin declare binding source=$RABBITMQ_EXCHANGE destination=$RABBITMQ_METRICS_QUEUE routing_key=$RABBITMQ_METRICS_ROUTING_KEY 