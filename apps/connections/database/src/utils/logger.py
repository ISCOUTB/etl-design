import logging
import logging.handlers
from pathlib import Path

from opentelemetry import trace
from pythonjsonlogger import jsonlogger

from src.core.config import settings

# Set basic logging configuration for the application
logging.basicConfig(level=logging.INFO)

# Ensure logs directory exists for file handlers
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)


class OTelContextFilter(logging.Filter):
    def __init__(
        self,
        *,
        service_name: str,
        service_version: str,
        environment: str,
        name: str = "",
    ) -> None:
        super().__init__(name)

        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment

    def filter(self, record: logging.LogRecord) -> bool:
        record.service_name = self.service_name
        record.service_version = self.service_version
        record.environment = self.environment

        span = trace.get_current_span()
        span_context = span.get_span_context()

        if span is not None and span_context is not None:
            record.trace_id = format(span_context.trace_id, "032x")
            record.span_id = format(span_context.span_id, "016x")
            record.trace_flags = format(span_context.trace_flags, "02x")
        else:
            record.trace_id = None
            record.span_id = None
            record.trace_flags = None

        return True


def setup_logger() -> logging.Logger:
    """Configure and return the main application logger.

    Sets up a comprehensive logging system with multiple handlers for different
    log levels and output destinations. The logger configuration includes:

    - Rotating file handler for general application logs
    - Daily rotating handler for day-based log organization
    - Error-specific handler for critical issue tracking
    - Console handler for real-time monitoring

    Log levels are configured based on the debug setting:
    - DEBUG mode: All log levels (DEBUG and above)
    - Production mode: ERROR level and above

    Returns:
        logging.Logger: Configured logger instance with all handlers attached

    Handler Configuration:
        - Rotating Handler: 10MB max size, 5 backup files, DEBUG level
        - Daily Handler: Midnight rotation, 30 days retention, INFO level
        - Error Handler: ERROR level only, persistent file
        - Console Handler: All levels, simplified formatting

    Note:
        The logger's propagate setting is disabled to prevent duplicate
        messages from parent loggers.
    """
    # Create main logger instance
    logger = logging.getLogger("Messaging Server")
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers to prevent duplication
    logger.handlers.clear()

    if settings.DATABASE_CONNECTION_DEBUG:
        # File formatter with timestamp and detailed context
        file_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [server] [Messaging] %(message)s"
        )

        # Rotating File Handler - Size-based rotation for main logs
        rotating_handler = logging.handlers.RotatingFileHandler(
            log_dir / "messaging_server.log",
            maxBytes=10 * 1024 * 1024,  # 10MB per file
            backupCount=5,  # Keep 5 backup files
            encoding="utf-8",
        )
        rotating_handler.setLevel(logging.DEBUG)
        rotating_handler.setFormatter(file_formatter)

        # Daily Rotating Handler - Time-based rotation for daily logs
        daily_handler = logging.handlers.TimedRotatingFileHandler(
            log_dir / "messaging_server_daily.log",
            when="midnight",  # Rotate at midnight
            interval=1,  # Every day
            backupCount=30,  # Keep 30 days of logs
            encoding="utf-8",
        )
        daily_handler.setLevel(logging.INFO)
        daily_handler.setFormatter(file_formatter)

        # Error File Handler - Dedicated error logging
        error_handler = logging.FileHandler(
            log_dir / "messaging_server_errors.log", encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)

        logger.addHandler(rotating_handler)
        logger.addHandler(daily_handler)
        logger.addHandler(error_handler)

    console_log_format = "[%(levelname)s] [server] [Messaging] %(message)s"
    json_format = (
        "%(asctime)s %(levelname)s %(name)s %(message)s "
        "%(service_name)s %(service_version)s %(environment)s "
        "%(trace_id)s %(span_id)s %(trace_flags)s "
        "%(module)s %(funcName)s"
    )

    console_formatter = (
        jsonlogger.JsonFormatter(json_format)  # type: ignore
        if not settings.DATABASE_CONNECTION_DEBUG
        else logging.Formatter(console_log_format)
    )

    # Console Handler - Real-time console output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(console_formatter)

    # Attach all handlers to the logger
    logger.addHandler(console_handler)

    otel_filter = OTelContextFilter(
        service_name="database-server",
        service_version="1.0.0",
        environment=("debug" if settings.DATABASE_CONNECTION_DEBUG else "production"),
    )
    logger.addFilter(otel_filter)

    # Disable propagation to prevent duplicate log messages
    logger.propagate = False
    return logger


# Global logger instance for application-wide use
logger = setup_logger()
