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

import json
import socket
import time

import grpc
import httpx
import pika
import psycopg
from messaging_utils.core.config import settings as mq_settings
from messaging_utils.messaging.connection_factory import (
    RabbitMQConnectionFactory,
)
from messaging_utils.schemas import InsertionMessage
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
from src.core.database_client import DatabaseClient, get_database_client
from src.core.events import failure_event
from src.schemas.workers import InsertionResult, ResultsMessage
from src.utils import create_component_logger, get_datetime_now, post_multipart_http
from src.workers.utils import get_task_status, update_task_status

# Create logger with [insertion] prefix
logger = create_component_logger("insertion")
tracer = trace.get_tracer("typechecking.insertion")


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
                        f"Schema worker connection error (attempt "
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
                logger.info("Schema worker interrupted by user.")
                self.stop_consuming()
                break

            except Exception as e:
                logger.error(f"Error starting schema worker: {repr(e)}")
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
            logger.info("Stopping schema Worker...")

            if self.channel and self.channel.is_open:
                self.channel.stop_consuming()
                RabbitMQConnectionFactory.close_thread_connections()
                logger.info("SchemaWorker: Connections closed")
        except Exception as e:
            logger.error(f"SchemaWorker: Error closing connections: {e}")

    def process_insertion_tasks(self, ch, method, properties, body) -> None:
        """Process incoming insertion task messages with idempotency guarantees.

        Implements robust idempotency by treating DB as the single source of truth.

        Critical Principle:
        - `set_task_id()` creates the FIRST state record in the database
        - All subsequent `update_task_status()` calls depend on this record existing
        - If `set_task_id()` fails, EVERYTHING fails → REQUEUE
        - This is NOT cache; it's the foundation record

        Three Error Categories:
        1. **CRITICAL Infrastructure Failures**: set_task_id/update_task_status failed
           → REQUEUE (DB is unavailable, can't proceed)
        2. **Logic Errors**: SQL errors, validation failures
           → Mark ERROR status, ACK (won't succeed on retry)
        3. **Non-Critical Failures**: Cache optimization failures
           → Log warning, continue (DB already correct, cache can be rebuilt)

        Args:
            ch: RabbitMQ channel object for message acknowledgment.
            method: Message delivery method containing delivery tag and routing info.
            properties: Message properties (headers, content-type, etc.).
            body: Raw message body containing the insertion request.

        Message Format:
            InsertionMessage with:
            - id: Task identifier
            - task: Task type (default: "sample_insertion")
            - file_data: Hex-encoded file content
            - table_name, project_id: Target table for insertion
            - db_uri: Database connection string
            - overwrite: Whether to overwrite existing data

        Idempotency:
            - Checks DB status before processing (prevents reprocessing)
            - Skips completed tasks (status in [success, error, published, completed])
            - Does NOT requeue when already processing (prevents duplicate work)
        """
        message = InsertionMessage(**json.loads(body.decode()))
        task_id = message["id"]
        task = message.get("task", "sample_insertion")
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
        span_cm = tracer.start_as_current_span("worker.insertion.process")
        span = span_cm.__enter__()
        span.set_attribute("messaging.system", "rabbitmq")
        span.set_attribute("messaging.operation", "process")
        span.set_attribute("task.id", task_id)
        span.set_attribute("task.type", task)

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

            # If task is already completed, it's safe to skip (idempotent)
            if current_status in ["success", "error", "completed"]:
                logger.info(
                    f"Task {task_id} already completed with status={current_status}. "
                    "ACK without reprocessing (idempotent)."
                )
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # If currently processing, likely another worker has it or it crashed.
            # Don't requeue to avoid duplicate processing.
            if current_status in [
                "received",
                "processing-file",
                "requesting-insert-sql",
                "file-processed",
                "received-schema-update",
            ]:
                logger.info(
                    f"Task {task_id} status={current_status} (processing). "
                    "Another worker is handling it. ACK and skip (prevents duplicate work)."
                )
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # --- PHASE 2: Initialize Task State if First Time (CRITICAL) ---
            # If task doesn't exist yet, create the foundation record
            if current_status is None:
                logger.info(
                    f"Task {task_id} first time processing, initializing state record"
                )
                try:
                    self.db_client.set_task_id(
                        dtypes.SetTaskIdRequest(
                            task_id=task_id,
                            value=dtypes.ApiResponse(
                                status="received",
                                code=202,
                                message="Task received and processing",
                                data={
                                    "task_id": task_id,
                                    "project_id": message["project_id"],
                                    "import_name": f"{message['project_id']}__{message['table_name']}",
                                },
                            ),
                            task=self.TASK,
                        )
                    )
                except (grpc.RpcError, ConnectionError, TimeoutError) as init_err:
                    # CRITICAL: Can't initialize task state - everything else depends on this
                    logger.error(
                        f"CRITICAL: Failed to initialize task {task_id} in DB: "
                        f"{type(init_err).__name__}: {init_err}. Requeueing."
                    )
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                    return
                except Exception as init_err:
                    logger.error(
                        f"CRITICAL: Unexpected error initializing task {task_id}: "
                        f"{type(init_err).__name__}: {init_err}. Requeueing."
                    )
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                    return

            # --- PHASE 3: Process Task (Business Logic) ---
            if task == "sample_insertion":
                logger.info(f"Starting insertion for task {task_id}")
                try:
                    result = self._insert_data(message, db_client=self.db_client)
                except (
                    grpc.RpcError,
                    httpx.ConnectError,
                    httpx.TimeoutException,
                    ConnectionError,
                    TimeoutError,
                ) as infra_err:
                    # Infrastructure error during processing (DB unavailable, timeout, etc.)
                    logger.error(
                        f"Infrastructure error processing insertion {task_id}: "
                        f"{type(infra_err).__name__}: {infra_err}. Requeueing."
                    )
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                    return
                except Exception as logic_err:
                    # SQL errors, validation failures, etc. - mark as error & ACK
                    logger.error(
                        f"Insertion logic error for task {task_id}: "
                        f"{type(logic_err).__name__}: {logic_err}. Marking as error."
                    )
                    try:
                        update_task_status(
                            database_client=self.db_client,
                            task_id=task_id,
                            field="status",
                            value="error",
                            task=self.TASK,
                            message=f"Insertion failed: {str(logic_err)}",
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
            else:
                logger.warning(f"Unknown task type '{task}' for task_id: {task_id}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # --- PHASE 4: Publish Results to DB (Atomic) ---
            try:
                self._publish_result(task_id, result, db_client=self.db_client)
            except (grpc.RpcError, ConnectionError, TimeoutError) as infra_err:
                # Infrastructure error publishing to DB
                logger.error(
                    f"Infrastructure error publishing insertion result {task_id}: "
                    f"{type(infra_err).__name__}: {infra_err}. Requeueing."
                )
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                return
            except Exception as pub_err:
                logger.error(
                    f"Error publishing result for task {task_id}: "
                    f"{type(pub_err).__name__}: {pub_err}"
                )
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # --- PHASE 5: Post-Processing (Cache Optimization - Non-Critical) ---
            # Update cache for faster subsequent reads (but DB is source of truth)
            try:
                self.db_client.set_task_id(
                    dtypes.SetTaskIdRequest(
                        task_id=task_id,
                        value=dtypes.ApiResponse(
                            status=result.get("status", "unknown"),
                            code=200,
                            message="Insertion completed",
                            data={
                                "task_id": task_id,
                                "results": json.dumps(result.get("results", {})),
                                "project_id": message["project_id"],
                                "import_name": f"{message['project_id']}__{message['table_name']}",
                            },
                        ),
                        task=self.TASK,
                    )
                )
            except (grpc.RpcError, ConnectionError, TimeoutError) as cache_err:
                # Cache update failed but DB state is already correct via update_task_status
                # Log and continue - this is optimization, not critical
                logger.warning(
                    f"Cache optimization failed for task {task_id} (non-critical): "
                    f"{type(cache_err).__name__}: {cache_err}. Continuing."
                )

            # --- PHASE 5: Acknowledge & Complete ---
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(
                f"Insertion completed successfully for task {task_id}. Message acknowledged."
            )

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

    def _insert_data(
        self, message: InsertionMessage, db_client: DatabaseClient
    ) -> InsertionResult:
        task_id = message["id"]
        project_id = message["project_id"]
        import_name = f"{project_id}__{message['table_name']}"
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
        table_name = message["table_name"]
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
            files = {"spreadsheet": (filename, file_bytes)}
            response = post_multipart_http(
                url=settings.EXCEL_READER_INSERT_URL,
                files=files,
                data={"table_name": table_name},
                params={"overwrite": overwrite},
                timeout_seconds=settings.EXCEL_READER_TIMEOUT_SECONDS,
                logger=logger,
                context=(
                    f"Error processing file for task {task_id} "
                    f"(url={settings.EXCEL_READER_INSERT_URL})"
                ),
            )

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
            return InsertionResult(
                task_id=task_id,
                project_id=project_id,
                import_name=import_name,
                results={},
                status="failed",
                error=str(e),
                traceparent=message.get("traceparent"),
                tracestate=message.get("tracestate"),
                baggage=message.get("baggage"),
            )

        try:
            with psycopg.connect(message["db_uri"]) as conn:
                cur = conn.cursor()
                for _, sql in sql_per_sheet.items():
                    cur.execute(sql)
                conn.commit()
        except Exception as e:
            logger.error(f"Error inserting data for task {task_id}: {e}")
            update_task_status(
                database_client=db_client,
                task_id=task_id,
                field="status",
                value="failed-inserting-data",
                task=self.TASK,
                data={"error": str(e), "update_date": get_datetime_now()},
            )
            return InsertionResult(
                task_id=task_id,
                project_id=project_id,
                import_name=import_name,
                results=sql_per_sheet,
                status="failed",
                error=str(e),
                traceparent=message.get("traceparent"),
                tracestate=message.get("tracestate"),
                baggage=message.get("baggage"),
            )

        return InsertionResult(
            task_id=task_id,
            project_id=project_id,
            import_name=import_name,
            results=sql_per_sheet,
            status="success",
            traceparent=message.get("traceparent"),
            tracestate=message.get("tracestate"),
            baggage=message.get("baggage"),
        )

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
        if self.channel is None:
            self.channel = RabbitMQConnectionFactory.get_thread_channel()

        self.channel.basic_publish(
            exchange=mq_settings.RABBITMQ_EXCHANGE,
            routing_key=mq_settings.RABBITMQ_PUBLISHERS_ROUTING_KEY_RESULTS,
            body=json.dumps(
                ResultsMessage(
                    task_id=task_id,
                    project_id=result["project_id"],
                    import_name=result["import_name"],
                    results=result["results"],
                    status=result["status"],
                    error=result.get("error", ""),
                    traceparent=result.get("traceparent"),
                    tracestate=result.get("tracestate"),
                    baggage=result.get("baggage"),
                )
            ).encode(),
        )
        update_task_status(
            database_client=db_client,
            task_id=task_id,
            field="status",
            value="published",
            task=self.TASK,
            message="Insertion result published",
            data={"update_date": get_datetime_now()},
        )
        logger.info(f"Insertion result published for task: {task_id}")
        return None
