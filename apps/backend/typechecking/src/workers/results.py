import asyncio
import json
import time
from typing import Any, Dict, Optional

import httpx
import pika
from messaging_utils.core.config import settings as mq_settings
from messaging_utils.messaging.connection_factory import (
    RabbitMQConnectionFactory,
)
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import (
    AMQPChannelError,
    AMQPConnectionError,
    ChannelClosedByBroker,
)

from src.core.config import settings
from src.core.database_client import get_database_client
from src.schemas.workers import ResultsMessage
from src.utils import create_component_logger, get_datetime_now
from src.workers.utils import update_task_status

# Create logger with [results] prefix
logger = create_component_logger("results")


class ResultWorker:
    TASK: str = "results"

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
        logger.info("Starting results worker...")
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
                    queue=mq_settings.RABBITMQ_QUEUE_RESULTS,
                    on_message_callback=self.process_results_request,
                    auto_ack=False,
                )

                logger.info("Results worker started. Waiting for messages...")

                connection_time = time.perf_counter() - t0
                logger.debug(
                    f"Results worker connected to RabbitMQ in {connection_time:.2f}s."
                )

                t0 = time.perf_counter()
                self.channel.start_consuming()

                # if start_consuming() returns, it means the worker was stopped normally
                logger.info("Results worker stopped consuming messages.")
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
                        f"Results worker connection error (attempt "
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
                logger.info("Results worker interrupted by user.")
                self.stop_consuming()
                break

            except Exception as e:
                logger.error(f"Error starting results worker: {repr(e)}")
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
            logger.info("Stopping results worker...")

            if self.db_client:
                self.db_client.close()

            if self.channel and self.channel.is_open:
                self.channel.stop_consuming()
                RabbitMQConnectionFactory.close_thread_connections()
                logger.info("ResultsWorker: Connections closed")
        except Exception as e:
            logger.error(f"ResultsWorker: Error closing connections: {e}")

    def process_results_request(
        self, ch: BlockingChannel, method, properties, body
    ) -> None:
        message = ResultsMessage(**json.loads(body))
        task_id = message["task_id"]
        logger.info(f"Processing results for task_id: {task_id}")

        # Do magic here...!
        asyncio.run(self._notify_task_completion(task_id, message, json.loads(body)))

        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(f"Results for task_id {task_id} processed and acknowledged.")

    async def _notify_task_completion(
        self, task_id: str, message: ResultsMessage, raw_data: Optional[Dict[str, Any]] = None
    ) -> None:
        try:
            async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    settings.API_REQUEST_URL,
                    json={
                        "task_id": task_id,
                        "status": message["status"],
                        "message": "Task completed with results",
                        "results": message["results"],
                        "raw_data": raw_data or {},  # Include raw_data if provided
                    },
                )
            response.raise_for_status()

            update_task_status(
                database_client=self.db_client,
                task_id=task_id,
                task=self.TASK,
                field="status",
                value="completed",
                data={
                    "results": json.dumps(message["results"]),
                    "status": message["status"],
                    "update_date": get_datetime_now(),
                },
            )
            logger.info(f"Task {task_id} marked as completed with results.")
        except Exception as e:
            logger.error(f"Error updating task status for task {task_id}: {repr(e)}")
            update_task_status(
                database_client=self.db_client,
                task_id=task_id,
                task=self.TASK,
                field="status",
                value="failed",
                data={"error": str(e), "update_date": get_datetime_now()},
            )
