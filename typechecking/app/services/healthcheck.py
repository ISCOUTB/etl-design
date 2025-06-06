import aio_pika
import asyncio
from typing import Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings


async def check_mongodb_connection() -> Dict[str, Any]:
    """Check MongoDB connection health."""
    try:
        mongo_url = str(settings.MONGO_URI)
        client = AsyncIOMotorClient(mongo_url)

        # Ping the database with a timeout
        await asyncio.wait_for(client.admin.command("ping"), timeout=5.0)

        # Get server info
        server_info = await client.server_info()
        await client.close()

        return {
            "status": "healthy",
            "version": server_info.get("version", "unknown"),
            "response_time_ms": "< 5000",
        }
    except asyncio.TimeoutError:
        return {
            "status": "unhealthy",
            "error": "Connection timeout",
            "response_time_ms": "> 5000",
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def check_rabbitmq_connection() -> Dict[str, Any]:
    """Check RabbitMQ connection health."""
    try:
        rabbitmq_url = str(settings.RABBITMQ_URI)

        # Connect with timeout
        connection = await asyncio.wait_for(
            aio_pika.connect_robust(rabbitmq_url), timeout=5.0
        )

        # Create a channel to test the connection
        channel = await connection.channel()
        await channel.close()
        await connection.close()

        return {"status": "healthy", "response_time_ms": "< 5000"}
    except asyncio.TimeoutError:
        return {
            "status": "unhealthy",
            "error": "Connection timeout",
            "response_time_ms": "> 5000",
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
