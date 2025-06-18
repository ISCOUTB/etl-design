"""Validation Worker Module.

This module provides a RabbitMQ worker that processes file validation messages
from the typechecking queue system. The ValidationWorker class handles incoming
validation requests, validates files against schemas, and publishes the results
back to the messaging system.

The worker processes uploaded files by converting hexadecimal data back to binary,
creating UploadFile objects, and running validation against specified schemas.
Results include detailed validation summaries and status information.

Example:
    Running the validation worker:

    >>> from app.workers.validation_workers import ValidationWorker
    >>> worker = ValidationWorker()
    >>> worker.start_consuming()  # Blocks and processes validation messages
"""

import json
import logging
import asyncio

from app.core.config import settings
from app.controllers.validation import (
    validate_file_against_schema,
    get_validation_summary,
)
from app.messaging.connection_factory import RabbitMQConnectionFactory
from app.core.database_redis import redis_db

from app.schemas.messaging import ValidationMessage
from app.schemas.workers import DataValidated

from fastapi import UploadFile
from io import BytesIO


logger = logging.getLogger(__name__)


class ValidationWorker:
    """RabbitMQ worker for processing file validation messages.

    This worker consumes messages from the 'typechecking.validation.queue',
    processes file validation requests by validating uploaded files against
    specified schemas, and publishes the validation results back to the exchange.

    The worker handles file data conversion from hexadecimal format back to
    binary, creates proper UploadFile objects, and runs comprehensive validation
    with detailed result summaries.

    Attributes:
        channel: RabbitMQ channel for message operations.
        publisher: ValidationPublisher instance for publishing results.
        connection: RabbitMQ connection established during consumption.
    """

    ENDPOINT: str = "validation"

    def start_consuming(self) -> None:
        """Start consuming messages from the RabbitMQ queue.

        Initializes the RabbitMQ connection and channel, sets up the messaging
        infrastructure, and begins consuming messages from the validation queue.
        This method blocks until consumption is stopped or an error occurs.

        The worker is configured with QoS settings to control message prefetch
        and uses manual acknowledgment for reliable message processing.

        Raises:
            Exception: If connection setup fails or consumption encounters
                unrecoverable errors. Errors are logged and consumption is stopped.
        """
        try:
            self.connection = RabbitMQConnectionFactory.get_thread_connection()
            self.channel = RabbitMQConnectionFactory.get_thread_channel()
            RabbitMQConnectionFactory.setup_infrastructure(self.channel)

            self.channel.basic_qos(prefetch_count=settings.WORKER_PREFETCH_COUNT)
            self.channel.basic_consume(
                queue="typechecking.validation.queue",
                on_message_callback=self.process_validation_request,
                auto_ack=False,
            )

            logger.info("Validation worker started. Waiting for messages...")
            self.channel.start_consuming()

        except Exception as e:
            logger.error(f"Error starting validation worker: {repr(e)}")
            self.stop_consuming()

    def stop_consuming(self) -> None:
        """Stop consuming messages and close the connection.

        Gracefully stops message consumption and closes RabbitMQ connections
        and channels. This method should be called during shutdown or when
        the worker needs to be stopped cleanly.

        Handles cases where connections may already be closed and logs
        the shutdown process for monitoring purposes.
        """
        try:
            if self.channel and self.channel.is_open:
                self.channel.stop_consuming()
                RabbitMQConnectionFactory.close_thread_connections()
                logger.info("ValidationWorker: Connections closed")
        except Exception as e:
            logger.error(f"ValidationWorker: Error closing connections: {e}")

    def process_validation_request(self, ch, method, properties, body) -> None:
        """Process a validation request message.

        Handles individual validation request messages by parsing the message body,
        extracting the task information, validating the file data, and publishing
        the result. Implements proper message acknowledgment on success and
        negative acknowledgment on failure.

        Args:
            ch: RabbitMQ channel object for message acknowledgment.
            method: Message delivery method containing delivery tag and routing info.
            properties: Message properties (headers, content-type, etc.).
            body: Raw message body containing the validation request.

        Message Format:
            Expected message body should be a JSON-encoded ApiResponse containing:
            - task_id: Unique identifier for the validation task
            - file_data: Hexadecimal-encoded file content
            - import_name: Schema identifier for validation
            - filename: Optional original filename

        Note:
            Failed messages are not requeued to prevent infinite retry loops.
            Error details are logged for debugging and monitoring.
        """
        try:
            message: ValidationMessage = json.loads(body.decode())
            task_id = message["id"]

            logger.info(f"Process validation request: {task_id}")

            result = asyncio.run(self._validate_data(message))
            self._publish_result(task_id, result)
            ch.basic_ack(delivery_tag=method.delivery_tag)

            logger.info(f"Validation completed for task: {task_id}")
        except Exception as e:
            logger.error(f"Error processing validation request: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    async def _validate_data(self, message: ValidationMessage) -> DataValidated:
        """Validate the incoming message data.

        Processes file validation by converting hexadecimal file data back to
        binary format, creating an UploadFile object, and running validation
        against the specified schema. Returns a structured validation result.

        Args:
            message: Dictionary containing validation parameters including:
                - task_id: Unique task identifier
                - file_data: Hexadecimal-encoded file content
                - import_name: Schema identifier for validation
                - filename: Optional original filename (defaults to 'uploaded_file')

        Returns:
            DataValidated: Dictionary containing the validation result with fields:
                - task_id: Original task identifier
                - status: Validation status ('valid', 'invalid', etc.)
                - results: Detailed validation summary including error counts,
                  validation details, and any schema violations

        Raises:
            Exception: If file conversion fails, validation encounters errors,
                or schema lookup fails. Errors are propagated to the caller
                for proper message handling.

        Note:
            This method is async due to the validate_file_against_schema
            function requiring async execution for file processing.
        """
        task_id = message["id"]
        redis_db.update_task_id(
            task_id=task_id,
            field="status",
            value="processing-file",
            endpoint=self.ENDPOINT,
        )
        file_bytes = bytes.fromhex(message["file_data"])
        file_obj = BytesIO(file_bytes)
        upload_file = UploadFile(
            filename=message.get("filename", "uploaded_file"), file=file_obj
        )

        redis_db.update_task_id(
            task_id=task_id,
            field="status",
            value="validating-file",
            endpoint=self.ENDPOINT,
        )

        results = await validate_file_against_schema(
            file=upload_file, import_name=message["import_name"]
        )
        summary = get_validation_summary(results)

        redis_db.update_task_id(
            task_id=task_id,
            field="status",
            value=summary["status"],
            endpoint=self.ENDPOINT,
            data={"results": summary},
        )

        return {
            "task_id": task_id,
            "status": summary["status"],
            "results": summary,
        }

    def _publish_result(self, task_id: str, result: DataValidated) -> None:
        """Publish the validation result back to the exchange.

        Sends the validation result to the 'typechecking.exchange' with
        routing key 'validation.result' for downstream consumers to process.

        Args:
            task_id: Unique identifier for the completed validation task,
                used for logging and correlation.
            result: Dictionary containing the validation result to be published.
                Should be JSON-serializable and contain validation summary data.

        Raises:
            Exception: If message publishing fails due to connection issues
                or serialization problems. Errors are propagated to the caller
                for proper error handling and message acknowledgment.
        """
        success = "success" if result["status"] == "completed" else "error"
        self.channel.basic_publish(
            exchange="typechecking.exchange",
            routing_key=f"results.validation.{success}",
            body=json.dumps(result),
        )
