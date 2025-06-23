#!/bin/sh

export PYTHONPATH=$PYTHONPATH:/app

cd /app/events_handler

uvicorn main:app --proxy-headers --host 0.0.0.0 --port $PROJECT_PORT
