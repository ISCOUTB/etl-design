import logging
import logging.handlers
from pathlib import Path

from opentelemetry import trace
from pythonjsonlogger import jsonlogger

from src.core.config import settings

# Ensure logs directory exists for file handlers
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Disable pika's verbose logging
logging.getLogger("pika").setLevel(logging.WARNING)


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


def create_component_logger(component_name: str) -> logging.Logger:
    """Create a logger with component-specific formatting.

    Args:
        component_name: Name of the component (e.g., 'main', 'validation', 'schemas')

    Returns:
        logging.Logger: Logger instance with component-specific prefix
    """
    component_logger = logging.getLogger(f"Typechecking.{component_name}")
    component_logger.setLevel(logging.DEBUG)  # Allow all levels

    # Clear any existing handlers
    component_logger.handlers.clear()

    if settings.MINIMAL_SERVER_DEBUG:
        # File formatter with component prefix
        file_formatter = logging.Formatter(
            f"[%(asctime)s] [%(levelname)s] [server] [Typechecking] [{component_name}] %(message)s"
        )

        # Component-specific rotating file handler
        rotating_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"typechecking_{component_name}.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        rotating_handler.setLevel(logging.DEBUG)
        rotating_handler.setFormatter(file_formatter)

        # Component-specific daily handler
        daily_handler = logging.handlers.TimedRotatingFileHandler(
            log_dir / f"typechecking_{component_name}_daily.log",
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8",
        )
        daily_handler.setLevel(logging.INFO)
        daily_handler.setFormatter(file_formatter)

        # Component-specific error handler
        error_handler = logging.FileHandler(
            log_dir / f"typechecking_{component_name}_errors.log", encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)

        # === CONSOLIDATED LOGS ===
        # Also write to the main consolidated log files

        # Consolidated rotating file handler
        consolidated_rotating_handler = logging.handlers.RotatingFileHandler(
            log_dir / "typechecking_server.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        consolidated_rotating_handler.setLevel(logging.DEBUG)
        consolidated_rotating_handler.setFormatter(file_formatter)

        # Consolidated daily handler
        consolidated_daily_handler = logging.handlers.TimedRotatingFileHandler(
            log_dir / "typechecking_server_daily.log",
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8",
        )
        consolidated_daily_handler.setLevel(logging.INFO)
        consolidated_daily_handler.setFormatter(file_formatter)

        # Consolidated error handler
        consolidated_error_handler = logging.FileHandler(
            log_dir / "typechecking_server_errors.log", encoding="utf-8"
        )
        consolidated_error_handler.setLevel(logging.ERROR)
        consolidated_error_handler.setFormatter(file_formatter)

        # Attach all handlers (component-specific + consolidated)
        component_logger.addHandler(rotating_handler)
        component_logger.addHandler(daily_handler)
        component_logger.addHandler(error_handler)

        # Add consolidated handlers
        component_logger.addHandler(consolidated_rotating_handler)
        component_logger.addHandler(consolidated_daily_handler)
        component_logger.addHandler(consolidated_error_handler)

    # Console formatter with component prefix
    json_format = (
        "%(asctime)s %(levelname)s %(name)s %(message)s "
        "%(service_name)s %(service_version)s %(environment)s "
        "%(trace_id)s %(span_id)s %(trace_flags)s "
        "%(module)s %(funcName)s"
    )
    console_log_format = (
        f"[%(levelname)s] [server] [Typechecking] [{component_name}] %(message)s"
    )

    console_formatter = (
        jsonlogger.JsonFormatter(json_format)  # type: ignore
        if not settings.MINIMAL_SERVER_DEBUG
        else logging.Formatter(console_log_format)
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Show INFO and above in console
    console_handler.setFormatter(console_formatter)

    component_logger.addHandler(console_handler)

    otel_filter = OTelContextFilter(
        service_name="TypecheckingServer",
        service_version=settings.OTEL_SERVICE_VERSION,
        environment="debug" if settings.MINIMAL_SERVER_DEBUG else "production",
    )
    component_logger.addFilter(otel_filter)

    # Disable propagation to prevent duplicate messages
    component_logger.propagate = False
    return component_logger
