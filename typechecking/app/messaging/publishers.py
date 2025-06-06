import json
import uuid
from typing import Any, Dict
from datetime import datetime

import pika
from app.messaging.connection import rabbitmq_connection
from app.schemas.messaging import ValidationMessage, SchemaMessage


class ValidationPublisher:
    """Publisher for validation messages."""

    def __init__(self):
        self._channel = rabbitmq_connection.channel

    def publish_validation_request(self, file_data: bytes, import_name: str, metadata: Dict[str, Any]) -> str:
        """Publish a validation request message to the RabbitMQ exchange."""
        task_id = str(uuid.uuid4())

        message: ValidationMessage = {
            "id": task_id,
            "timestamp": datetime.now().isoformat(),
            "file_data": file_data.hex(),
            "import_name": import_name,
            "metadata": metadata,
            "priority": metadata.get("priority", 5),
        }

        self._channel.basic_publish(
            exchange="typechecking.exchange",
            routing_key="validation.request",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                message_id=task_id,
                timestamp=int(datetime.now().timestamp()),
                delivery_mode=pika.DeliveryMode.Persistent,
                priority=message["priority"]
            )
        )

        return task_id

    def publish_schema_update(self, schema: Dict, import_name: str) -> str:
        """Publish a schema update message to the RabbitMQ exchange."""
        task_id = str(uuid.uuid4())

        message: SchemaMessage = {
            "id": task_id,
            "timestamp": datetime.now().isoformat(),
            "schema": schema,
            "import_name": import_name,
        }

        self._channel.basic_publish(
            exchange="typechecking.exchange",
            routing_key="schema.update",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                message_id=task_id,
                timestamp=int(datetime.now().timestamp()),
                delivery_mode=pika.DeliveryMode.Persistent
            )
        )

        return task_id
