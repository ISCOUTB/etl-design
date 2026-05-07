#!/bin/bash
source scripts/.env

CONTAINER_NAME=typechecking-redis

if [ "$(docker ps -a -q -f name=^/${CONTAINER_NAME}$)" ]; then
  docker start $CONTAINER_NAME
  exit 0
fi

docker run -d \
  --name $CONTAINER_NAME \
  -p "${REDIS_PORT}:6379" \
  --restart on-failure \
  -v typechecking_redis_data:/data \
  -e REDIS_PASSWORD=${REDIS_PASSWORD} \
  redis:7.4.1 redis-server --requirepass "${REDIS_PASSWORD}"
