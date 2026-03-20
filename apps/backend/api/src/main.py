import shutil
from contextlib import asynccontextmanager

import grpc
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pika.exceptions import AMQPError
from prometheus_fastapi_instrumentator import Instrumentator

from src.api.exceptions import (
    app_exception_handler,
    grpc_exception_handler,
    rabbitmq_exception_handler,
)
from src.api.main import router as api_router
from src.api.middlewares import LogsMiddleware
from src.core.config import settings
from src.exceptions import AppException
from src.utils.logger import LOGGING_CONFIG


@asynccontextmanager
async def lifespan(app: FastAPI):
    def _separator(char: str = "=", width: int = shutil.get_terminal_size().columns):
        print(char * width)

    if settings.SERVER_DEBUG:
        _separator()
        print("URL MAP - Registered Routes")
        _separator()
        for route in app.routes:
            if hasattr(route, "methods"):
                methods = ", ".join(sorted(route.methods))  # type: ignore
                print(f"{methods:8} -> {route.path}")  # type: ignore
        _separator()

    yield


app = FastAPI(
    title="S.L.O.T.H API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Register Prometheus middleware and metrics route before startup.
Instrumentator().instrument(app).expose(app, endpoint=f"{settings.API_V1_STR}/metrics")

if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR, tags=["api"])

app.add_exception_handler(grpc.RpcError, grpc_exception_handler)
app.add_exception_handler(AMQPError, rabbitmq_exception_handler)
app.add_exception_handler(AppException, app_exception_handler)

# Add logging middleware at the end to ensure it captures all logs from other middlewares and routes.
# only applies when it's not in debug mode, since in debug mode the logs will be duplicated
if not settings.SERVER_DEBUG:
    app.add_middleware(LogsMiddleware)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.SERVER_DEBUG,
        reload_dirs=["src"] if settings.SERVER_DEBUG else None,
        reload_includes=["*.py"] if settings.SERVER_DEBUG else None,
        log_config=LOGGING_CONFIG,
        log_level="debug",
        use_colors=True,
    )
