"""Schema Worker Module.

This module provides a RabbitMQ worker that processes schema update messages
from the typechecking queue system. The SchemaWorker class handles incoming
schema update requests, processes them by creating and saving schemas, and
publishes the results back to the messaging system.

The worker implements proper message acknowledgment, error handling, and
connection management using the RabbitMQ connection factory for thread safety.

Example:
    Running the schema worker:

    >>> from src.workers.schemas import SchemaWorker
    >>> worker = SchemaWorker()
    >>> worker.start_consuming()  # Blocks and processes messages
"""

import asyncio
import json
import time

import httpx
import pika
import psycopg2
from messaging_utils.core.config import settings as mq_settings
from messaging_utils.messaging.connection_factory import (
    RabbitMQConnectionFactory,
)
from messaging_utils.schemas import InsertionMessage
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import (
    AMQPChannelError,
    AMQPConnectionError,
    ChannelClosedByBroker,
)
from proto_utils.database import dtypes

from src.core.config import settings
from src.core.database_client import DatabaseClient, get_database_client
from src.schemas.workers import InsertionResult
from src.utils import create_component_logger, get_datetime_now
from src.workers.utils import update_task_status

# Create logger with [insertion] prefix
logger = create_component_logger("insertion")


class InsertionWorker:
    """RabbitMQ worker for processing schema update messages.

    This worker consumes messages from the 'typechecking.schema.queue',
    processes schema update requests by creating and saving schemas,
    and publishes the results back to the exchange for further processing.

    The worker handles message acknowledgment, error recovery, and maintains
    proper connection lifecycle management through the connection factory.

    Attributes:
        max_retries: Maximum number of retries for processing a message.
        retry_delay: Initial delay between retries in seconds.
        backoff: Backoff multiplier for retry delays.
        threshold: Time threshold to reset retry attempts.
        db_client: Database client for task status updates.
        connection: RabbitMQ blocking connection for the worker thread.
        channel: RabbitMQ channel for message operations.
    """

    TASK = "insertion"

    def __init__(
        self,
        max_retries: int,
        retry_delay: float,
        backoff: float,
        threshold: float,
    ) -> None:
        """Initialize the SchemaWorker instance.

        Sets up initial state for the worker, including connection and channel
        placeholders. Actual connection setup is performed in start_consuming().
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff = backoff
        self.threshold = threshold

        self.db_client = get_database_client(logger)
        self.connection: pika.BlockingConnection | None = None
        self.channel: BlockingChannel | None = None

    def start_consuming(self) -> None:
        """Start consuming messages from the RabbitMQ queue with intelligent retry.

        Implements time-based retry strategy with exponential backoff. Distinguishes
        between immediate connection failures and stable connections that later fail.
        Resets retry counter if connection was stable for >= threshold seconds,
        preventing exit after temporary hiccups in long-running workers.

        The worker fails fast after exhausting retries, allowing the orchestrator
        to restart the container with fresh state.

        Retry Strategy:
            - Max retries configurable (default: 5)
            - Exponential backoff (2s → 4s → 8s → 16s → 32s)
            - Stability threshold (default: 60s)
            - Counter resets if uptime >= threshold

        Connection Lifecycle:
            1. Attempt connection with exponential backoff
            2. Start consuming (blocks until connection lost)
            3. On disconnect, check elapsed uptime:
               - If >= threshold: reset retry counter (stable connection)
               - If < threshold: increment counter (unstable/flapping)
            4. Retry or fail-fast if max retries exhausted

        Raises:
            SystemExit: After exhausting retries, exits with code 1 for orchestrator
                restart. Implements fail-fast pattern.
            KeyboardInterrupt: Handled gracefully for manual shutdown.
        """
        logger.info("Starting schema worker...")
        attempts = 0
        current_delay = self.retry_delay
        t0 = time.perf_counter()
        while attempts < self.max_retries:
            try:
                self.connection = RabbitMQConnectionFactory.get_thread_connection()
                self.channel = RabbitMQConnectionFactory.get_thread_channel()
                RabbitMQConnectionFactory.setup_infrastructure(self.channel)

                self.channel.basic_qos(prefetch_count=settings.WORKER_PREFETCH_COUNT)
                self.channel.basic_consume(
                    queue=mq_settings.RABBITMQ_QUEUE_INSERTION,
                    on_message_callback=self.process_insertion_tasks,
                    auto_ack=False,
                )

                logger.info("Schema worker started. Waiting for messages...")
                connection_time = time.perf_counter() - t0
                logger.debug(
                    f"Schema worker connected to RabbitMQ in {connection_time:.2f}s."
                )

                t0 = time.perf_counter()
                self.channel.start_consuming()

                # if start_consuming() returns, it means the worker was stopped normally
                logger.info("Schema worker stopped consuming messages.")
                break

            except (
                AMQPConnectionError,
                AMQPChannelError,
                ChannelClosedByBroker,
            ) as e:
                elapsed_time = time.perf_counter() - t0
                if elapsed_time >= self.threshold:
                    logger.info(
                        f"Connection was stable for {elapsed_time:.1f}s. "
                        "Resetting retry counter."
                    )
                    attempts = 0
                    current_delay = self.retry_delay

                if attempts < self.max_retries:
                    logger.warning(
                        f"Schema worker connection error (attempt "
                        f"{attempts + 1}/{self.max_retries}): {repr(e)}. "
                        f"Retrying in {current_delay}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= self.backoff
                    t0 = time.perf_counter()
                else:
                    logger.error(
                        f"Failed to connect to RabbitMQ after "
                        f"{self.max_retries} attempts. "
                        f"Last error: {repr(e)}. "
                        "Exiting. Orchestrator should restart this worker."
                    )
                    self.stop_consuming()
                    raise SystemExit(1) from e

                attempts += 1

            except KeyboardInterrupt:
                logger.info("Schema worker interrupted by user.")
                self.stop_consuming()
                break

            except Exception as e:
                logger.error(f"Error starting schema worker: {repr(e)}")
                self.stop_consuming()
                raise SystemExit(1) from e

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
            logger.info("Stopping schema Worker...")

            if self.db_client:
                self.db_client.close()

            if self.channel and self.channel.is_open:
                self.channel.stop_consuming()
                RabbitMQConnectionFactory.close_thread_connections()
                logger.info("SchemaWorker: Connections closed")
        except Exception as e:
            logger.error(f"SchemaWorker: Error closing connections: {e}")

    def process_insertion_tasks(self, ch, method, properties, body) -> None:
        """Process incoming insertion task messages from RabbitMQ.

        Args:
            ch: RabbitMQ channel object for message acknowledgment.
            method: Message delivery method containing delivery tag and routing info.
            properties: Message properties (headers, content-type, etc.).
            body: Raw message body containing the schema update request.

        Message Format:
            Expected message body should be a JSON-encoded ApiResponse containing:
            - task_id: Unique identifier for the schema update task
            - import_name: Name identifier for the schema import
            - schema_params: Parameters needed to create the schema

        Note:
            Failed messages are not requeued to prevent infinite retry loops.
            Error details are logged for debugging and monitoring.
        """
        try:
            message = InsertionMessage(**json.loads(body.decode()))
            task_id = message["id"]
            task = message.get("task", "sample_insertion")

            if task == "sample_insertion":
                logger.info(f"Processing sample insertion: {task_id}")
                update_task_status(
                    database_client=self.db_client,
                    task_id=task_id,
                    field="status",
                    value="received-schema-update",
                    task=self.TASK,
                    data={
                        "upload_date": message["date"],
                        "update_date": get_datetime_now(),
                    },
                )
                result = asyncio.run(
                    self._insert_data(message, db_client=self.db_client)
                )
            else:
                logger.warning(f"Unknown task type '{task}' for task_id: {task_id}")
                raise ValueError(f"Unknown task type: {task}")

            # Add more cases here if needed for other tasks

            self._publish_result(task_id, result, db_client=self.db_client)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Schema update completed for task: {task_id}")
        except Exception as e:
            logger.error(f"Error processing schema update: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    async def _insert_data(
        self, message: InsertionMessage, db_client: DatabaseClient
    ) -> InsertionResult:
        task_id = message["id"]
        update_task_status(
            database_client=db_client,
            task_id=task_id,
            field="status",
            value="processing-file",
            task=self.TASK,
            data={"update_date": get_datetime_now()},
        )

        file_bytes = bytes.fromhex(message["file_data"])
        filename = message["metadata"]["filename"]
        table_name = message["project_id"]
        overwrite = message["overwrite"]

        update_task_status(
            database_client=db_client,
            task_id=task_id,
            field="status",
            value="requesting-insert-sql",
            task=self.TASK,
            data={"update_date": get_datetime_now()},
        )

        try:
            # Maybe here we can use httpx.Timeout to be more specific
            async with httpx.AsyncClient(
                timeout=settings.EXCEL_READER_TIMEOUT_SECONDS
            ) as client:
                files = {"spreadsheet": (filename, file_bytes)}
                response = await client.post(
                    settings.EXCEL_READER_INSERT_URL,
                    files=files,
                    data={"table_name": table_name},
                    params={"overwrite": overwrite},
                )

            response.raise_for_status()
            sql_per_sheet = response.json()

            update_task_status(
                database_client=db_client,
                task_id=task_id,
                field="status",
                value="file-processed",
                task=self.TASK,
                data={"update_date": get_datetime_now()},
            )

        except Exception as e:
            logger.error(f"Error processing file for task {task_id}: {e}")
            update_task_status(
                database_client=db_client,
                task_id=task_id,
                field="status",
                value="failed-processing-file",
                task=self.TASK,
                data={"error": str(e), "update_date": get_datetime_now()},
            )
            return InsertionResult(task_id=task_id, results={}, status="failed")

        with psycopg2.connect(message["db_uri"]) as conn:
            cur = conn.cursor()
            for _, sql in sql_per_sheet.items():
                cur.execute(sql)
            conn.commit()

        return InsertionResult(task_id=task_id, results=sql_per_sheet, status="success")

    def _publish_result(
        self, task_id: str, result: InsertionResult, db_client: DatabaseClient
    ) -> None:
        """Publish the result of the schema update to the RabbitMQ exchange.

        Sends the schema update result to the 'typechecking.exchange' with
        routing key 'schema.result' for downstream consumers to process.

        Args:
            task_id (str): Unique identifier for the completed task, used for logging.
            result (InsertionResult): Dictionary containing the schema update result to be published.
            db_client (DatabaseClient): Database client for task status updates.

        Raises:
            Exception: If message publishing fails due to connection issues
                or serialization problems. Errors are propagated to the caller
                for proper error handling and message acknowledgment.
        """
        if result["status"] != "success":
            task_get_result = db_client.get_task_id(
                dtypes.GetTaskIdRequest(
                    task_id=task_id,
                    task=self.TASK,
                )
            )
            assert task_get_result["found"] and task_get_result["value"] is not None

            upload_date = task_get_result["value"]["data"].get(
                "upload_date", get_datetime_now()
            )
            update_task_status(
                database_client=db_client,
                task_id=task_id,
                field="status",
                value="failed-publishing-result",
                task=self.TASK,
                message="Failed to publish validation result",
                data={
                    "error": "Failed to publish validation result",
                    "update_date": get_datetime_now(),
                    "upload_date": upload_date,
                },
                reset_data=True,
            )
            logger.error(f"Failed to publish result for task: {task_id}")
            return None

        self.channel.basic_publish(
            exchange=mq_settings.RABBITMQ_EXCHANGE,
            routing_key=mq_settings.RABBITMQ_PUBLISHERS_ROUTING_KEY_RESULTS,
            body=json.dumps(result),
        )
        update_task_status(
            database_client=db_client,
            task_id=task_id,
            field="status",
            value="published",
            task=self.TASK,
            message="Validation result published",
            data={"update_date": get_datetime_now()},
        )
        logger.info(f"Validation result published for task: {task_id}")
        return None
