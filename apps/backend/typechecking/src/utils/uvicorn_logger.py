"""Uvicorn logging configuration for minimal HTTP server.

This module keeps Uvicorn/FastAPI logging aligned with the component logger:
- Minimal debug mode: human-readable console + file handlers (component and consolidated)
- Production mode: JSON console output only
"""

from pathlib import Path
from typing import Any, Dict

from src.core.config import settings

# Ensure logs directory exists
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

_uvicorn_base_handlers = ["default"]
_uvicorn_access_handlers = ["access"]
_root_handlers = ["default"]
_minimal_server_handlers = ["default"]

if settings.MINIMAL_SERVER_DEBUG:
    _uvicorn_base_handlers.extend(
        [
            "file",
            "daily",
            "error",
            "consolidated_file",
            "consolidated_daily",
            "consolidated_error",
        ]
    )
    _uvicorn_access_handlers.extend(
        ["file", "daily", "consolidated_file", "consolidated_daily"]
    )
    _root_handlers.extend(
        [
            "file",
            "daily",
            "error",
            "consolidated_file",
            "consolidated_daily",
            "consolidated_error",
        ]
    )
    _minimal_server_handlers.extend(
        [
            "file",
            "daily",
            "error",
            "consolidated_file",
            "consolidated_daily",
            "consolidated_error",
        ]
    )

    formatters_config = {
        "default": {
            "format": "[%(levelname)s] [server] [Typechecking] [http-server] %(message)s",
        },
        "access": {
            "format": "[%(levelname)s] [server] [Typechecking] [http-server] %(message)s",
        },
        "file": {
            "format": "[%(asctime)s] [%(levelname)s] [server] [Typechecking] [http-server] %(message)s",
        },
    }
    extra_handlers_config = {
        # Component-specific file handlers
        "file": {
            "formatter": "file",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(log_dir / "typechecking_http-server.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
        },
        "daily": {
            "formatter": "file",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(log_dir / "typechecking_http-server_daily.log"),
            "when": "midnight",
            "interval": 1,
            "backupCount": 30,
            "encoding": "utf-8",
        },
        "error": {
            "formatter": "file",
            "class": "logging.FileHandler",
            "filename": str(log_dir / "typechecking_http-server_errors.log"),
            "encoding": "utf-8",
            "level": "ERROR",
        },
        # Consolidated file handlers (shared with other components)
        "consolidated_file": {
            "formatter": "file",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(log_dir / "typechecking_server.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
        },
        "consolidated_daily": {
            "formatter": "file",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(log_dir / "typechecking_server_daily.log"),
            "when": "midnight",
            "interval": 1,
            "backupCount": 30,
            "encoding": "utf-8",
        },
        "consolidated_error": {
            "formatter": "file",
            "class": "logging.FileHandler",
            "filename": str(log_dir / "typechecking_server_errors.log"),
            "encoding": "utf-8",
            "level": "ERROR",
        },
    }
else:
    formatters_config = {
        "default": {
            "class": "pythonjsonlogger.json.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s %(module)s %(funcName)s",
        },
        "access": {
            "class": "pythonjsonlogger.json.JsonFormatter",
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
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "class": "logging.StreamHandler",
            "formatter": "access",
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
        "src.minimal_server": {
            "handlers": _minimal_server_handlers,
            "level": "INFO",
            "propagate": False,
        },
        "pika": {
            "handlers": _root_handlers,
            "level": "WARNING",
            "propagate": False,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": _root_handlers,
    },
}
