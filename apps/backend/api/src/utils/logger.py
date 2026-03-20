import logging
import logging.handlers
from pathlib import Path
from typing import Any, Dict

from opentelemetry import trace
from pythonjsonlogger import jsonlogger

from src.core.config import settings

# Ensure logs directory exists
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
    console_log_format = "[%(levelname)s] [server] [API] %(message)s"
    json_format = (
        "%(asctime)s %(levelname)s %(name)s %(message)s "
        "%(service_name)s %(service_version)s %(environment)s "
        "%(trace_id)s %(span_id)s %(trace_flags)s "
        "%(module)s %(funcName)s"
    )

    console_formatter = (
        jsonlogger.JsonFormatter(json_format)  # type: ignore
        if not settings.SERVER_DEBUG
        else logging.Formatter(console_log_format)
    )

    # Create main logger instance
    logger = logging.getLogger("API")

    # Adjust log level based on debug configuration
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers to prevent duplication
    logger.handlers.clear()

    if settings.SERVER_DEBUG:
        # File formatter with timestamp and detailed context
        file_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [server] [API] %(message)s"
        )

        # Rotating File Handler - Size-based rotation for main logs
        rotating_handler = logging.handlers.RotatingFileHandler(
            log_dir / "api_server.log",
            maxBytes=10 * 1024 * 1024,  # 10MB per file
            backupCount=5,  # Keep 5 backup files
            encoding="utf-8",
        )
        rotating_handler.setLevel(logging.DEBUG)
        rotating_handler.setFormatter(file_formatter)

        # Daily Rotating Handler - Time-based rotation for daily logs
        daily_handler = logging.handlers.TimedRotatingFileHandler(
            log_dir / "api_server_daily.log",
            when="midnight",  # Rotate at midnight
            interval=1,  # Every day
            backupCount=30,  # Keep 30 days of logs
            encoding="utf-8",
        )
        daily_handler.setLevel(logging.INFO)
        daily_handler.setFormatter(file_formatter)

        # Error File Handler - Dedicated error logging
        error_handler = logging.FileHandler(
            log_dir / "api_server_errors.log", encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)

        logger.addHandler(rotating_handler)
        logger.addHandler(daily_handler)
        logger.addHandler(error_handler)

    # Console Handler - Real-time console output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(console_formatter)

    # Attach all handlers to the logger
    logger.addHandler(console_handler)

    otel_filter = OTelContextFilter(
        service_name="api-server",
        service_version="1.0.0",
        environment="debug" if settings.SERVER_DEBUG else "production",
    )
    logger.addFilter(otel_filter)

    # Disable propagation to prevent duplicate log messages
    logger.propagate = False
    return logger


# Global logger instance for application-wide use
logger = setup_logger()

_uvicorn_base_handlers = ["default"]
_uvicorn_access_handlers = ["access"]
_root_handlers = ["default"]
_sqlalchemy_handlers = []
_pika_handlers = []

if settings.SERVER_DEBUG:
    _uvicorn_base_handlers.extend(["file", "daily", "error"])
    _root_handlers.extend(["file", "daily", "error"])
    _sqlalchemy_handlers.extend(["file", "error"])
    _pika_handlers.extend(["file", "error"])

    formatters_config = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(message)s",
            "use_colors": None,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
        },
        "file": {
            "format": "[%(asctime)s] [%(levelname)s] [server] [API] %(name)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "access_file": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '[%(asctime)s] [%(levelname)s] [server] [API] [access] %(client_addr)s - "%(request_line)s" %(status_code)s',
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    # File handlers for persistent logging
    extra_handlers_config = {
        "file": {
            "formatter": "file",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(log_dir / "api_server.log"),
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8",
        },
        "daily": {
            "formatter": "file",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(log_dir / "api_server_daily.log"),
            "when": "midnight",
            "interval": 1,
            "backupCount": 30,
            "encoding": "utf-8",
        },
        "error": {
            "formatter": "file",
            "class": "logging.FileHandler",
            "filename": str(log_dir / "api_server_errors.log"),
            "encoding": "utf-8",
            "level": "ERROR",
        },
        "access_file": {
            "formatter": "access_file",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(log_dir / "api_access.log"),
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8",
        },
    }
else:
    formatters_config = {
        "default": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s %(module)s %(funcName)s",
        },
        "access": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(client_addr)s %(request_line)s %(status_code)s",
        },
    }
    extra_handlers_config = {}

LOGGING_CONFIG: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": formatters_config,
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        **extra_handlers_config,
    },
    "loggers": {
        "uvicorn": {
            "handlers": _uvicorn_base_handlers,
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": _uvicorn_base_handlers,
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": _uvicorn_access_handlers,
            "level": "INFO",
            "propagate": False,
        },
        # Add custom loggers for your API components
        "API": {
            "handlers": _root_handlers,
            "level": "INFO",
            "propagate": False,
        },
        # Silence noisy third-party loggers
        "sqlalchemy.engine": {
            "handlers": _sqlalchemy_handlers,
            "level": "WARNING",
            "propagate": False,
        },
        "sqlalchemy.pool": {
            "handlers": _sqlalchemy_handlers,
            "level": "WARNING",
            "propagate": False,
        },
        "pika": {
            "handlers": _pika_handlers,
            "level": "WARNING",
            "propagate": False,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": _root_handlers,
    },
}
