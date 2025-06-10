import pika
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class RabbitMQConnection:
    _instance: Optional["RabbitMQConnection"] = None
    _connection: Optional[pika.BlockingConnection] = None
    _channel: Optional[pika.channel.Channel] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self) -> bool:
        """Establish a connection to RabbitMQ server."""
        try:
            connection_params = pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                virtual_host=settings.RABBITMQ_VHOST,
                credentials=pika.PlainCredentials(
                    username=settings.RABBITMQ_USER, password=settings.RABBITMQ_PASSWORD
                ),
                heartbeat=600,
                blocked_connection_timeout=300,
            )

            self._connection = pika.BlockingConnection(connection_params)
            self._channel = self._connection.channel()

            # Declare exchanges and queues
            self._setup_messaging_infrastructure()
            return True

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False

    def _setup_messaging_infrastructure(self) -> None:
        """Set up exchanges and queues for messaging."""
        self._channel.exchange_declare(
            exchange="typechecking.exchange", exchange_type="topic", durable=True
        )

        queues = [
            "typechecking.validation.queue",
            "typechecking.schema.queue",
            "typechecking.results.queue",
        ]

        for queue in queues:
            self._channel.queue_declare(queue=queue, durable=True)

        self._channel.queue_bind(
            exchange="typechecking.exchange",
            queue="typechecking.validation.queue",
            routing_key="validation.*",
        )

        self._channel.queue_bind(
            exchange="typechecking.exchange",
            queue="typechecking.schema.queue",
            routing_key="schema.*",
        )

    @property
    def channel(self) -> pika.channel.Channel:
        """Get the RabbitMQ channel."""
        if not self._channel or self._channel.is_closed:
            self.connect()
        return self._channel

    def close(self) -> None:
        """Close the RabbitMQ connection."""
        if self._channel and self._channel.is_open:
            self._channel.close()
            logger.info("RabbitMQ channel closed.")

        if self._connection and self._connection.is_open:
            self._connection.close()
            logger.info("RabbitMQ connection closed.")


rabbitmq_connection = RabbitMQConnection()
