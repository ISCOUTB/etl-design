"""RabbitMQ connection parameters configuration module.

This module constructs a complete messaging parameters response object that
contains all necessary information for clients to connect to and interact
with the RabbitMQ message broker. It transforms application settings into
the standardized protocol buffer format used by gRPC clients.

Constants:
    messaging_params: Complete messaging configuration including connection
                     details, exchange information, and queue definitions

The messaging_params object serves as the authoritative source for all
RabbitMQ configuration distributed to clients via the GetMessagingParams
gRPC endpoint.
"""

from messaging_utils.core.config import settings
from messaging_utils.core.constants import (
    RABBITMQ_DELIVARY_LIMIT,
    RABBITMQ_DURABLE_EXCHANGE,
    RABBITMQ_DURABLE_QUEUES,
    RABBITMQ_EXCHANGE_TYPE,
    RABBITMQ_MESSAGE_TTL_MS,
    RABBITMQ_QUEUE_TYPE,
)
from messaging_utils.schemas.connection import (
    AllConnectionParams,
    ExchangeInfo,
    QueueInfo,
)

# Complete messaging parameters configuration for client distribution
messaging_params = AllConnectionParams(
    host=settings.RABBITMQ_HOST,
    port=settings.RABBITMQ_PORT,
    username=settings.RABBITMQ_USER,
    password=settings.RABBITMQ_PASSWORD,
    virtual_host=settings.RABBITMQ_VHOST,
    exchange=ExchangeInfo(
        exchange=settings.RABBITMQ_EXCHANGE,
        durable=RABBITMQ_DURABLE_EXCHANGE,
        type=RABBITMQ_EXCHANGE_TYPE,
        queues=[
            # Schema message queue configuration
            QueueInfo(
                queue=settings.RABBITMQ_QUEUE_INSERTION,
                routing_key=settings.RABBITMQ_ROUTING_KEY_INSERTION,
                durable=RABBITMQ_DURABLE_QUEUES,
                queue_type=RABBITMQ_QUEUE_TYPE,
                delivery_limit=RABBITMQ_DELIVARY_LIMIT,
                message_ttl_ms=RABBITMQ_MESSAGE_TTL_MS,
            ),
            # Validation message queue configuration
            QueueInfo(
                queue=settings.RABBITMQ_QUEUE_VALIDATIONS,
                routing_key=settings.RABBITMQ_ROUTING_KEY_VALIDATIONS,
                durable=RABBITMQ_DURABLE_QUEUES,
                queue_type=RABBITMQ_QUEUE_TYPE,
                delivery_limit=RABBITMQ_DELIVARY_LIMIT,
                message_ttl_ms=RABBITMQ_MESSAGE_TTL_MS,
            ),
            # Results queue configuration
            QueueInfo(
                queue=settings.RABBITMQ_QUEUE_RESULTS,
                routing_key=settings.RABBITMQ_ROUTING_KEY_RESULTS,
                durable=RABBITMQ_DURABLE_QUEUES,
                queue_type=RABBITMQ_QUEUE_TYPE,
                delivery_limit=RABBITMQ_DELIVARY_LIMIT,
                message_ttl_ms=RABBITMQ_MESSAGE_TTL_MS,
            ),
        ],
    ),
)
