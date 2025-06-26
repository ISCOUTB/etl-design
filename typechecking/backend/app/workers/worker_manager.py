"""Worker Manager Module.

This module provides a centralized manager for running multiple RabbitMQ workers
in separate threads. The WorkerManager class coordinates the lifecycle of
validation and schema workers, handles graceful shutdown, and manages the
overall worker process.

The manager uses threading to run workers concurrently while maintaining proper
signal handling for clean shutdown operations. It supports both programmatic
control and signal-based termination.

Example:
    Running the worker manager:

    >>> import asyncio
    >>> from app.workers.worker_manager import WorkerManager
    >>>
    >>> async def run_workers():
    ...     manager = WorkerManager()
    ...     await manager.start_workers()
    >>>
    >>> asyncio.run(run_workers())

    Or run directly:
    >>> python -m app.workers.worker_manager
"""

import asyncio
import signal
import sys
import threading
import logging

from app.workers.validation_workers import ValidationWorker
from app.workers.schema_workers import SchemaPublisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkerManager:
    """Manager for coordinating multiple RabbitMQ workers.

    This class manages the lifecycle of validation and schema workers,
    running them in separate daemon threads while providing centralized
    control for starting, monitoring, and stopping the workers.

    The manager handles graceful shutdown, error logging, and maintains
    the main process alive while workers are running.

    Attributes:
        validation_worker: ValidationWorker instance for processing validation messages.
        schema_worker: SchemaPublisher instance for processing schema messages.
        workers_running: Boolean flag controlling the main loop execution.
    """

    def __init__(self):
        """Initialize the WorkerManager.

        Creates instances of validation and schema workers and sets up
        the initial state for worker management. Workers are not started
        until start_workers() is called.
        """
        self.validation_worker = ValidationWorker()
        self.schema_worker = SchemaPublisher()
        self.workers_running = True

    async def start_workers(self):
        """Start all worker threads.

        Launches validation and schema workers in separate daemon threads
        and maintains the main process alive while workers are running.
        The method handles KeyboardInterrupt for graceful shutdown.

        The main thread sleeps in short intervals to remain responsive
        to shutdown signals while allowing workers to process messages
        in their respective threads.

        Raises:
            KeyboardInterrupt: Caught and handled gracefully by stopping workers.
            Exception: Other exceptions are logged but may terminate the process.

        Note:
            This method blocks until workers are stopped or an interrupt occurs.
            Worker threads are created as daemon threads to ensure clean process
            termination when the main thread exits.
        """
        try:
            # Start validation worker in a separate thread
            validation_thread = threading.Thread(
                target=self._run_validation_worker, name="ValidationWorker", daemon=True
            )
            validation_thread.start()

            # Start schema worker in a separate thread
            schema_thread = threading.Thread(
                target=self._run_schema_worker, name="SchemaWorker", daemon=True
            )
            schema_thread.start()

            logger.info("All workers started successfully")

            # Keep main thread alive
            while self.workers_running:
                await asyncio.sleep(0.5)

        except KeyboardInterrupt:
            logger.info("Shutting down workers...")
            self.stop_workers()

    def _run_validation_worker(self):
        """Run validation worker.

        Internal method that starts the validation worker's message consumption.
        This method is executed in a separate thread and handles any exceptions
        that occur during worker execution.

        Exceptions are logged but do not stop other workers, allowing the
        system to continue operating with reduced functionality if one
        worker fails.
        """
        try:
            print("Consuming validation worker")
            self.validation_worker.start_consuming()
        except Exception as e:
            logger.error(f"Validation worker error: {e}")

    def _run_schema_worker(self):
        """Run schema worker.

        Internal method that starts the schema worker's message consumption.
        This method is executed in a separate thread and handles any exceptions
        that occur during worker execution.

        Exceptions are logged but do not stop other workers, allowing the
        system to continue operating with reduced functionality if one
        worker fails.
        """
        try:
            print("Consuming schema worker")
            self.schema_worker.start_consuming()
        except Exception as e:
            logger.error(f"Schema worker error: {e}")

    def stop_workers(self):
        """Stop all workers gracefully.

        Sets the workers_running flag to False, which causes the main loop
        in start_workers() to exit. This provides a clean shutdown mechanism
        for the worker manager.

        Individual workers handle their own connection cleanup when their
        consuming loops are interrupted.
        """
        self.workers_running = False
        logger.info("Workers stopped")


def signal_handler(signum, frame):
    """Handle shutdown signals.

    Signal handler for SIGINT and SIGTERM that provides clean shutdown
    functionality. When these signals are received, the process exits
    gracefully after logging the signal number.

    Args:
        signum: Signal number that was received.
        frame: Current stack frame (unused).

    Note:
        This handler calls sys.exit(0) which triggers normal Python cleanup
        including daemon thread termination and resource cleanup.
    """
    logger.info(f"Received signal {signum}")
    sys.exit(0)


async def main() -> None:
    """Main entry point for the worker manager.

    Sets up signal handlers for graceful shutdown and starts the worker
    manager. This function serves as the primary entry point when the
    module is run directly.

    Signal handlers are registered for SIGINT (Ctrl+C) and SIGTERM
    to ensure clean shutdown in both interactive and service environments.

    Raises:
        Exception: Any unhandled exceptions from worker startup or execution
            are allowed to propagate and will terminate the process.
    """
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start worker manager
    manager = WorkerManager()
    await manager.start_workers()


if __name__ == "__main__":
    asyncio.run(main())
