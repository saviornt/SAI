# backend/database/redis.py

from redis import asyncio as aioredis
import os
import asyncio
import signal
from utils import configure_logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = configure_logging()

# Redis Connection
REDIS_URI = os.getenv("REDIS_URI", "redis://localhost:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Initialize Redis client
redis_pool = None

async def redis_init():
    """
    Initialize the Redis connection.

    This function attempts to create a connection pool to Redis.
    """
    global redis_pool
    retries = 3
    for attempt in range(retries):
        try:
            logger.info("Initializing Redis connection...")
            redis_pool = await aioredis.from_url(
                REDIS_URI,
                password=REDIS_PASSWORD,
                max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", 10)),
                decode_responses=True
            )
            logger.info("Successfully connected to Redis.")
            break
        except Exception as e:
            logger.exception(f"Exception occurred during Redis initialization: {e}")
            if attempt < retries - 1:
                logger.info(f"Retrying Redis connection... (Attempt {attempt + 2}/{retries})")
                await asyncio.sleep(5)
            else:
                logger.error("Failed to connect to Redis after multiple attempts.")

async def redis_close():
    """
    Close the Redis connection.

    This function ensures that the Redis connection is properly closed when no longer needed.
    """
    global redis_pool
    if redis_pool is not None:
        logger.info("Closing Redis connection...")
        await redis_pool.close()
        logger.info("Redis connection closed.")

# Register the close_connection function to be called during application shutdown
def register_shutdown_events(loop):
    assert loop is not None, "Event loop is not available."
    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.ensure_future(redis_close()))
    except NotImplementedError:
        logger.warning("Signal handlers are not available in the current environment. Make sure to close Redis connection manually if needed.")

# Register the shutdown events
loop = asyncio.get_running_loop()
register_shutdown_events(loop)
