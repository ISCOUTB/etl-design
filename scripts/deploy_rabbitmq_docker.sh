# !/bin/bash
source .env
docker run -d --name typechecking-rabbitmq \
  -p "${RABBITMQ_PORT}:5672" \
  -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=${RABBITMQ_USER} \
  -e RABBITMQ_DEFAULT_PASS=${RABBITMQ_PASSWORD} \
  -v typechecking_rabbitmq_data:/var/lib/rabbitmq \
  rabbitmq:4-management
