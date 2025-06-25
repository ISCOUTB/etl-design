import asyncio
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from app.services.healthcheck import (
    check_mongodb_connection,
    check_rabbitmq_connection,
    check_redis_connection,
    check_postgres_connection,
)

import json
from app.core.database_redis import redis_db

router = APIRouter()


@router.get("")
async def healthcheck(use_cache: bool = True) -> Dict[str, Any]:
    """
    Comprehensive health check endpoint that verifies:
    - API status
    - MongoDB connection
    - RabbitMQ connection
    """
    if use_cache and (cached_health := redis_db.get("healthcheck")):
        return json.loads(cached_health)

    try:
        # Run health checks concurrently
        healthchecks = await asyncio.gather(
            check_mongodb_connection(),
            check_rabbitmq_connection(),
            check_redis_connection(),
            check_postgres_connection(),
            return_exceptions=True,
        )

        mongodb_check, rabbitmq_check, redisdb_check, postgres_check = healthchecks

        # Handle exceptions from gather
        if isinstance(mongodb_check, Exception):
            mongodb_check = {"status": "unhealthy", "error": str(mongodb_check)}

        if isinstance(rabbitmq_check, Exception):
            rabbitmq_check = {"status": "unhealthy", "error": str(rabbitmq_check)}

        if isinstance(redisdb_check, Exception):
            redisdb_check = {"status": "unhealthy", "error": str(redisdb_check)}

        if isinstance(postgres_check, Exception):
            postgres_check = {"status": "unhealthy", "error": str(postgres_check)}

        # Determine overall health
        overall_status = "healthy"
        if (
            mongodb_check["status"] != "healthy"
            or rabbitmq_check["status"] != "healthy"
            or redisdb_check["status"] != "healthy"
        ):
            overall_status = "degraded"

        health_report = {
            "status": overall_status,
            "timestamp": asyncio.get_event_loop().time(),
            "services": {
                "api": {"status": "healthy", "message": "API is running"},
                "mongodb": mongodb_check,
                "rabbitmq": rabbitmq_check,
                "redisdb": redisdb_check,
                "postgres": postgres_check,
            },
        }

        # Return 503 if any service is unhealthy
        if overall_status == "degraded":
            raise HTTPException(status_code=503, detail=health_report)

        redis_db.set("healthcheck", json.dumps(health_report), ex=60)
        return health_report
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
    cached_health = redis_db.get("healthcheck_simple")
    if cached_health:
        return json.loads(cached_health)

    response = {"status": "ok", "message": "API is running"}
    redis_db.set("healthcheck_simple", json.dumps(response), ex=60)
    return response
