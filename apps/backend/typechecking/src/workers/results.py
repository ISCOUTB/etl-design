import json
import socket
import time
from typing import Any, Dict, Optional

import grpc
import httpx
import pika
from messaging_utils.core.config import settings as mq_settings
from messaging_utils.messaging.connection_factory import (
    RabbitMQConnectionFactory,
)
from opentelemetry import context as otel_context
from opentelemetry import trace
from opentelemetry.propagate import extract
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import (
    AMQPChannelError,
    AMQPConnectionError,
    ChannelClosedByBroker,
)
from proto_utils.database import dtypes

from src.core.config import settings
from src.core.database_client import get_database_client
from src.core.events import failure_event
from src.schemas.workers import ResultsMessage
from src.utils import (
    create_component_logger,
    get_datetime_now,
    post_json_http_with_ssl_fallback,
)
from src.workers.utils import get_task_status, update_task_status

# Create logger with [results] prefix
logger = create_component_logger("results")
tracer = trace.get_tracer("typechecking.results")


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
                socket.gaierror,
            ) as e:
                elapsed_time = time.perf_counter() - t0
                if elapsed_time >= self.threshold:
                    logger.info(
                        f"Connection was stable for {elapsed_time:.1f}s. "
                        "Resetting retry counter."
                    )
                    attempts = 0
                    current_delay = self.retry_delay

                attempt_number = attempts + 1
                if attempt_number < self.max_retries:
                    logger.warning(
                        f"Results worker connection error (attempt "
                        f"{attempt_number}/{self.max_retries}): {repr(e)}. "
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

                    failure_event.set()  # Signal failure to main thread
                    raise SystemExit(1) from e

                attempts += 1

            except KeyboardInterrupt:
                logger.info("Results worker interrupted by user.")
                self.stop_consuming()
                break

            except Exception as e:
                logger.error(f"Error starting results worker: {repr(e)}")
                self.stop_consuming()

                failure_event.set()  # Signal failure to main thread
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
            if self.channel and self.channel.is_open:
                self.channel.stop_consuming()
                RabbitMQConnectionFactory.close_thread_connections()
                logger.info("ResultsWorker: Connections closed")
        except Exception as e:
            logger.error(f"ResultsWorker: Error closing connections: {e}")

    def process_results_request(
        self, ch: BlockingChannel, method, properties, body
    ) -> None:
        """Process results messages with idempotency guarantees.

        Implements robust idempotency by treating DB as the single source of truth.

        Critical Principle:
        - `set_task_id()` creates the FIRST state record in the database
        - All subsequent `update_task_status()` calls depend on this record existing
        - If `set_task_id()` fails, EVERYTHING fails → REQUEUE
        - This is NOT cache; it's the foundation record

        Three Error Categories:
        1. **CRITICAL Infrastructure Failures**: set_task_id/update_task_status failed
           → REQUEUE (DB is unavailable, can't proceed)
        2. **Logic Errors**: API notification failed
           → Mark ERROR status, ACK (don't retry - prevents duplicate notifications)
        3. **Non-Critical Failures**: Cache optimization failures
           → Log warning, continue (DB already correct, cache can be rebuilt)

        Args:
            ch: RabbitMQ channel object for message acknowledgment.
            method: Message delivery method containing delivery tag and routing info.
            properties: Message properties (headers, content-type, etc.).
            body: Raw message body containing the results.

        Message Format:
            ResultsMessage with:
            - task_id: Task identifier
            - status: Final status of the task
            - results: Detailed results data to send to API

        Idempotency:
            - Checks DB status before processing (prevents duplicate notifications)
            - Skips already completed tasks (status = "completed")
            - Does NOT requeue when already notifying (prevents duplicate API calls)
        """
        message = ResultsMessage(**json.loads(body))
        task_id = message["task_id"]
        traceparent = message.get("traceparent")
        tracestate = message.get("tracestate")
        baggage = message.get("baggage")
        extracted_context = extract(
            {
                "traceparent": traceparent,
                "tracestate": tracestate,
                "baggage": baggage,
            }
        )
        token = otel_context.attach(extracted_context)
        span_cm = tracer.start_as_current_span("worker.results.process")
        span = span_cm.__enter__()
        span.set_attribute("messaging.system", "rabbitmq")
        span.set_attribute("messaging.operation", "process")
        span.set_attribute("task.id", task_id)
        logger.info(f"Processing results for task_id: {task_id}")
        try:
            # --- PHASE 1: Idempotency Check (consult DB as source of truth) ---
            try:
                current_status = get_task_status(
                    task_id=task_id,
                    task=self.TASK,
                    database_client=self.db_client,
                )
            except Exception as db_err:
                logger.error(
                    f"Failed to fetch task status for {task_id}: {db_err}. "
                    "Requeueing to retry later."
                )
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                return

            # If task is already completed, it's safe to skip (idempotent - API already notified)
            if current_status == "completed":
                logger.info(
                    f"Task {task_id} already marked as completed. "
                    "API already notified. ACK without reprocessing (idempotent)."
                )
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # If currently notifying, another worker likely has it.
            # Don't requeue to prevent duplicate API notifications.
            if current_status == "notifying":
                logger.info(
                    f"Task {task_id} status=notifying (in progress). "
                    "Another worker is notifying the API. ACK and skip (prevents duplicate calls)."
                )
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # --- PHASE 2: Initialize Task State Record (CRITICAL Foundation) ---
            # Create first task state record in DB if this is the first time processing
            if current_status is None:
                try:
                    self.db_client.set_task_id(
                        dtypes.SetTaskIdRequest(
                            task_id=task_id,
                            value=dtypes.ApiResponse(
                                status="received",
                                code=200,
                                message="Task received for results processing",
                                data={"update_date": get_datetime_now()},
                            ),
                            task=self.TASK,
                        )
                    )
                    logger.debug(
                        f"Task {task_id} foundation record created in DB (status=received)."
                    )
                except (grpc.RpcError, ConnectionError, TimeoutError) as init_err:
                    # Critical failure: cannot create foundation record
                    logger.error(
                        f"Failed to initialize task {task_id} foundation record: "
                        f"{type(init_err).__name__}: {init_err}. "
                        "REQUEUE (critical infrastructure failure)."
                    )
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                    return

            # --- PHASE 3: Notify API (Business Logic & Mark Result) ---
            try:
                # Mark as notifying to prevent other workers from processing
                update_task_status(
                    database_client=self.db_client,
                    task_id=task_id,
                    task=self.TASK,
                    field="status",
                    value="notifying",
                    data={"update_date": get_datetime_now()},
                )

                # Do the actual notification work
                self._notify_task_completion(task_id, message, json.loads(body))
            except (
                grpc.RpcError,
                httpx.ConnectError,
                httpx.TimeoutException,
                ConnectionError,
                TimeoutError,
            ) as infra_err:
                # Infrastructure error during notification (API/DB unavailable, timeout)
                logger.error(
                    f"Infrastructure error notifying API for task {task_id}: "
                    f"{type(infra_err).__name__}: {infra_err}. Requeueing."
                )
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                return
            except Exception as logic_err:
                # Unexpected error during notification - mark as error & ACK
                logger.error(
                    f"Error notifying API for task {task_id}: "
                    f"{type(logic_err).__name__}: {logic_err}. Marking as error."
                )
                try:
                    update_task_status(
                        database_client=self.db_client,
                        task_id=task_id,
                        task=self.TASK,
                        field="status",
                        value="error",
                        message=f"Notification failed: {str(logic_err)}",
                        data={
                            "error": str(logic_err),
                            "update_date": get_datetime_now(),
                        },
                    )
                except Exception as status_err:
                    logger.error(
                        f"Failed to mark task {task_id} as error: {status_err}"
                    )
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # --- PHASE 4: Acknowledge & Complete ---
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Results for task_id {task_id} processed and acknowledged.")

        except (
            grpc.RpcError,
            httpx.ConnectError,
            httpx.TimeoutException,
            ConnectionError,
            TimeoutError,
        ) as e:
            # Catch-all for infrastructure errors at top level
            logger.error(
                f"Infrastructure error for task {task_id}: {type(e).__name__} - {e}. "
                "Requeueing for retry."
            )
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        except Exception as e:
            # Unexpected error at top level - log and ACK to prevent stuck message
            logger.error(
                f"Unexpected error processing task {task_id}: {type(e).__name__} - {e}. "
                "ACK to prevent message from stuck indefinitely."
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)

        finally:
            span_cm.__exit__(None, None, None)
            otel_context.detach(token)

    def _notify_task_completion(
        self,
        task_id: str,
        message: ResultsMessage,
        raw_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        status_code: int | str = "unknown"
        error_detail = message.get("error")
        if not error_detail and raw_data:
            error_detail = raw_data.get("error")

        completion_message = "Task completed with results"
        if message["status"].lower() != "success":
            completion_message = (
                f"Task failed: {error_detail}"
                if error_detail
                else "Task failed"
            )

        payload = {
            "task_id": task_id,
            "status": message["status"],
            "message": completion_message,
            "results": message["results"],
            "raw_data": raw_data or {},  # Include raw_data if provided
        }

        try:
            status_code = post_json_http_with_ssl_fallback(
                url=settings.API_REQUEST_URL,
                payload=payload,
                timeout_seconds=settings.API_TIMEOUT_SECONDS,
                logger=logger,
                context=(
                    f"Main API request failed for task {task_id} "
                    f"(url={settings.API_REQUEST_URL})"
                ),
            )
        except Exception as e:
            logger.error(
                f"Main API request failed for task {task_id} "
                f"(url={settings.API_REQUEST_URL}): {type(e).__name__}: {repr(e)}"
            )
            update_task_status(
                database_client=self.db_client,
                task_id=task_id,
                task=self.TASK,
                field="status",
                value="failed",
                data={"error": str(e), "update_date": get_datetime_now()},
            )
            return

        try:
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
            logger.error(
                f"Main API notified (status={status_code}) but failed updating "
                f"task state for {task_id}: {type(e).__name__}: {repr(e)}"
            )
            update_task_status(
                database_client=self.db_client,
                task_id=task_id,
                task=self.TASK,
                field="status",
                value="failed",
                data={"error": str(e), "update_date": get_datetime_now()},
            )
