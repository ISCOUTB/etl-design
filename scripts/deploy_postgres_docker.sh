#!/bin/bash
source scripts/.env

CONTAINER_NAME=typechecking-postgres

if [ "$(docker ps -a -q -f name=^/${CONTAINER_NAME}$)" ]; then
  docker start $CONTAINER_NAME
  exit 0
fi

docker run -d --name $CONTAINER_NAME \
  -p "${POSTGRES_PORT}:5432" \
  -e POSTGRES_USER=${POSTGRES_USER} \
  -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
  -e PGDATA=/var/lib/postgresql/data/pgdata \
  -e POSTGRES_DB=${POSTGRES_DB} \
  -v typechecking_postgres_data:/var/lib/postgresql/data/pgdata \
  postgres:18

