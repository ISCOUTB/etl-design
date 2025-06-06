import asyncio
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from app.services.healthcheck import check_mongodb_connection, check_rabbitmq_connection

router = APIRouter()


@router.get("/")
async def healthcheck() -> Dict[str, Any]:
    """
    Comprehensive health check endpoint that verifies:
    - API status
    - MongoDB connection
    - RabbitMQ connection
    """
    try:
        # Run health checks concurrently
        mongodb_check, rabbitmq_check = await asyncio.gather(
            check_mongodb_connection(),
            check_rabbitmq_connection(),
            return_exceptions=True,
        )

        # Handle exceptions from gather
        if isinstance(mongodb_check, Exception):
            mongodb_check = {"status": "unhealthy", "error": str(mongodb_check)}

        if isinstance(rabbitmq_check, Exception):
            rabbitmq_check = {"status": "unhealthy", "error": str(rabbitmq_check)}

        # Determine overall health
        overall_status = "healthy"
        if (
            mongodb_check["status"] != "healthy"
            or rabbitmq_check["status"] != "healthy"
        ):
            overall_status = "degraded"

        health_report = {
            "status": overall_status,
            "timestamp": asyncio.get_event_loop().time(),
            "services": {
                "api": {"status": "healthy", "message": "API is running"},
                "mongodb": mongodb_check,
                "rabbitmq": rabbitmq_check,
            },
        }

        # Return 503 if any service is unhealthy
        if overall_status == "degraded":
            raise HTTPException(status_code=503, detail=health_report)

        return health_report

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "unhealthy",
                "error": f"Health check failed: {str(e)}",
                "services": {"api": {"status": "unhealthy", "error": str(e)}},
            },
        )


@router.get("/simple")
async def simple_healthcheck() -> dict:
    """
    Simple health check endpoint for basic API status.
    """
    return {"status": "ok", "message": "API is running"}
