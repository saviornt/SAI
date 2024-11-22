# backend/database/mongo.py

import motor.motor_asyncio
import os
import asyncio
import signal
from utils import configure_logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = configure_logging()

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "sai")

# Initialize MongoDB client and database with connection pooling
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(
    MONGO_URI,
    maxPoolSize=int(os.getenv("MONGO_MAX_POOL_SIZE", 100)),
    minPoolSize=int(os.getenv("MONGO_MIN_POOL_SIZE", 10))
)
mongo_db = mongo_client[MONGO_DB_NAME]

async def mongo_init():
    """
    Initialize the MongoDB connection and ensure that the necessary collections exist.

    This function attempts to connect to MongoDB and create the required collections if they don't exist.
    """
    retries = 3
    for attempt in range(retries):
        try:
            logger.info("Initializing MongoDB connection...")
            await mongo_client.admin.command('ping')
            logger.info("Successfully connected to MongoDB.")

            # Create necessary collections if they don't exist
            collections = ["logs", "users", "projects"]
            existing_collections = await mongo_db.list_collection_names()
            for collection in collections:
                if collection not in existing_collections:
                    await mongo_db.create_collection(collection)
                    logger.info(f"Created collection: {collection}")
            break
        except Exception as e:
            logger.exception(f"Exception occurred during MongoDB initialization: {e}")
            if attempt < retries - 1:
                logger.info(f"Retrying MongoDB connection... (Attempt {attempt + 2}/{retries})")
                await asyncio.sleep(5)
            else:
                logger.error("Failed to connect to MongoDB after multiple attempts.")

async def mongo_close():
    """
    Close the MongoDB connection.

    This function ensures that the MongoDB client connection is properly closed when no longer needed.
    """
    logger.info("Closing MongoDB connection...")
    mongo_client.close()
    logger.info("MongoDB connection closed.")

# Register the close_connection function to be called during application shutdown
def register_shutdown_events(loop):
    assert loop is not None
    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            if hasattr(loop, 'add_signal_handler'):
                loop.add_signal_handler(sig, lambda: asyncio.create_task(mongo_close()))
    except NotImplementedError:
        logger.warning("Signal handlers are not available in the current environment. Make sure to close MongoDB connection manually if needed.")

# Register the shutdown events
loop = asyncio.get_event_loop()
register_shutdown_events(loop)
