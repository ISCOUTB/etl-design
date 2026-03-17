#!/bin/bash
source scripts/.env

CONTAINER_NAME=typechecking-rabbitmq

if [ "$(docker ps -a -q -f name=^/${CONTAINER_NAME}$)" ]; then
  docker start $CONTAINER_NAME
  exit 0
fi

docker run -d --name $CONTAINER_NAME \
  -p "${RABBITMQ_PORT}:5672" \
  -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=${RABBITMQ_USER} \
  -e RABBITMQ_DEFAULT_PASS=${RABBITMQ_PASSWORD} \
  -v typechecking_rabbitmq_data:/var/lib/rabbitmq \
  rabbitmq:4-management
