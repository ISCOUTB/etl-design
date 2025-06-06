import json
import logging
from typing import Any, Dict

from app.core.config import settings
from app.schemas.workers import SchemaUpdated
from app.controllers.schemas import save_schema, create_schema

import pika.channel
from app.messaging.connection import rabbitmq_connection
from app.messaging.publishers import ValidationPublisher

logger = logging.getLogger(__name__)


class SchemaPublisher:
    def __init__(self) -> None:
        self.channel: pika.channel.Channel = rabbitmq_connection.channel
        self.publisher = ValidationPublisher()
    
    def start_consuming(self) -> None:
        """Start consuming messages from the RabbitMQ queue."""
        self.channel.basic_qos(prefetch_count=settings.WORKER_PREFETCH_COUNT)

        self.channel.basic_consume(
            queue="typechecking.schema.queue",
            on_message_callback=self.process_schema_update,
            auto_ack=False
        )

        logger.info("Schema worker started. Waiting for messages...")
        self.channel.start_consuming()

    def process_schema_update(self, ch, method, properties, body) -> None:
        try:
            message = json.loads(body.decode())
            task_id = message["id"]

            logger.info(f"Processing schema update: {task_id}")

            result = self._update_schema(message)
            self._publish_result(task_id, result)
            ch.basic_ack(delivery_tag=method.delivery_tag)

            logger.info(f"Schema update completed for task: {task_id}")
        except Exception as e:
            logger.error(f"Error processing schema update: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def _update_schema(self, message: Dict[str, Any]) -> SchemaUpdated:
        """Update the schema based on the incoming message."""
        import_name = message["import_name"]
        schema = create_schema(message["schema_params"])
        result = save_schema(schema, import_name)
        status = "completed" if result else "failed"

        return {
            "task_id": message["id"],
            "status": status,
            "import_name": import_name,
            "schema": schema,
            "result": result
        }

    def _publish_result(self, task_id: str, result: Dict) -> None:
        """Publish the result of the schema update to the RabbitMQ exchange."""
        logger.info(f"Publishing schema update result for task: {task_id}")
        self.channel.basic_publish(
            exchange="typechecking.exchange",
            routing_key="schema.result",
            body=json.dumps(result)
        )
