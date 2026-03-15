RABBITMQ_EXCHANGE_TYPE: str = "topic"
RABBITMQ_DURABLE_EXCHANGE: bool = True
RABBITMQ_DURABLE_QUEUES: bool = True

# Use quorum queues for better reliability and message durability
RABBITMQ_QUEUE_TYPE: str = "quorum"

# Queue arguments for message TTL and delivery limits
RABBITMQ_DELIVARY_LIMIT: int = 3

# Only apply for quorum queues
RABBITMQ_MESSAGE_TTL_MS: int = 3600 * 1000  # 1 hour in milliseconds
