"""RabbitMQ Connection Manager Module.

This module provides a singleton RabbitMQ connection manager that handles
establishing and maintaining connections to RabbitMQ server. It sets up
the necessary messaging infrastructure including exchanges and queues
for the typechecking application.

Example:
    Basic usage of the RabbitMQ connection:

    >>> from app.messaging.connection import rabbitmq_connection
    >>> if rabbitmq_connection.connect():
    ...     channel = rabbitmq_connection.channel
    ...     # Use channel for messaging operations
    ...     rabbitmq_connection.close()
"""

import pika
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class RabbitMQConnection:
    """Singleton RabbitMQ connection manager.

    This class implements the singleton pattern to ensure only one
    RabbitMQ connection exists throughout the application lifecycle.
    It manages the connection, channel, and messaging infrastructure setup.

    Attributes:
        _instance: Class-level singleton instance holder.
        _connection: Active RabbitMQ blocking connection.
        _channel: Active RabbitMQ channel for messaging operations.
    """

    _instance: Optional["RabbitMQConnection"] = None
    _connection: Optional[pika.BlockingConnection] = None
    _channel: Optional[pika.channel.Channel] = None

    def __new__(cls):
        """Create or return existing singleton instance.

        Returns:
            RabbitMQConnection: The singleton instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self) -> bool:
        """Establish a connection to RabbitMQ server.

        Creates a blocking connection to RabbitMQ using configuration
        settings and sets up the messaging infrastructure including
        exchanges and queues.

        Returns:
            bool: True if connection was successful, False otherwise.

        Raises:
            Exception: Connection errors are caught and logged, but not re-raised.
        """
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
        """Set up exchanges and queues for messaging.

        Declares the main exchange and required queues for the typechecking
        application. Also sets up queue bindings with appropriate routing keys.

        Exchanges created:
            - typechecking.exchange: Topic exchange for routing messages

        Queues created:
            - typechecking.validation.queue: For validation-related messages
            - typechecking.schema.queue: For schema-related messages
            - typechecking.results.queue: For processing results

        Raises:
            pika.exceptions.AMQPError: If exchange or queue declaration fails.
        """
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
        """Get the RabbitMQ channel.

        Returns the active channel, automatically reconnecting if the
        channel is closed or doesn't exist.

        Returns:
            pika.channel.Channel: Active RabbitMQ channel for messaging operations.

        Raises:
            Exception: If reconnection fails when channel is closed.
        """
        if not self._channel or self._channel.is_closed:
            self.connect()
        return self._channel

    def close(self) -> None:
        """Close the RabbitMQ connection.

        Safely closes the channel and connection if they are open.
        Logs the closure operations for monitoring purposes.
        """
        if self._channel and self._channel.is_open:
            self._channel.close()
            logger.info("RabbitMQ channel closed.")

        if self._connection and self._connection.is_open:
            self._connection.close()
            logger.info("RabbitMQ connection closed.")


# Global singleton instance for application-wide use
rabbitmq_connection = RabbitMQConnection()
