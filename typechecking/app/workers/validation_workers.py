import json
import logging
from typing import Dict, Any

from app.core.config import settings
from app.controllers.validation import (
    validate_file_against_schema,
    get_validation_summary,
)

import pika.channel
from app.messaging.publishers import ValidationPublisher
from app.messaging.connection import rabbitmq_connection
from app.schemas.workers import DataValidated

from fastapi import UploadFile
from io import BytesIO


logger = logging.getLogger(__name__)


class ValidationWorker:
    def __init__(self) -> None:
        self.channel: pika.channel.Channel = rabbitmq_connection.channel
        self.publisher = ValidationPublisher()

    def start_consuming(self) -> None:
        """Start consuming messages from the RabbitMQ queue."""
        self.channel.basic_qos(prefetch_count=settings.WORKER_PREFETCH_COUNT)

        self.channel.basic_consume(
            queue="typechecking.validation.queue",
            on_message_callback=self.process_validation_request,
            auto_ack=False,
        )

        logger.info("Validation worker started. Waiting for messages...")
        self.channel.start_consuming()

    def process_validation_request(self, ch, method, properties, body) -> None:
        """Process a validation request message."""
        try:
            message = json.loads(body.decode())
            task_id = message["task_id"]

            logger.info(f"Process validation request: {task_id}")

            result = self._validate_data(message)
            self._publish_result(task_id, result)
            ch.basic_ack(delivery_tag=method.delivery_tag)

            logger.info(f"Validation completed for task: {task_id}")
        except Exception as e:
            logger.error(f"Error processing validation request: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    async def _validate_data(self, message: Dict[str, Any]) -> DataValidated:
        """Validate the incoming message data."""
        file_bytes = bytes.fromhex(message["file_data"])
        file_obj = BytesIO(file_bytes)
        upload_file = UploadFile(
            filename=message.get("filename", "uploaded_file"), file=file_obj
        )

        results = await validate_file_against_schema(
            file=upload_file, import_name=message["import_name"]
        )
        summary = get_validation_summary(results)

        return {
            "task_id": message["task_id"],
            "status": summary["status"],
            "results": summary,
        }

    def _publish_result(self, task_id: str, result: Dict) -> None:
        """Publish the validation result back to the exchange."""
        self.channel.basic_publish(
            exchange="typechecking.exchange",
            routing_key="validation.result",
            body=json.dumps(result),
        )
